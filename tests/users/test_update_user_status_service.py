# -*- coding: utf-8 -*-

# ======================================================================
# tests/users/test_update_user_status_service.py
# ======================================================================

from unittest.mock import MagicMock

import pytest

from tests.conftest import make_user
from app.modules.users.services.users import UpdateUserStatusService


def _make(user):
    repo = MagicMock()
    repo.get_by_id.return_value = user
    repo.update.side_effect = lambda u: u
    repo.get_role_info.return_value = {"code": "investor", "name": "Inversor"}
    return UpdateUserStatusService(repo=repo), repo


class TestUpdateUserStatusService:

    @pytest.mark.parametrize("status", ["blocked", "disabled"])
    def test_deactivating_revokes_session_and_pending_code(self, status):
        user = make_user(id=5, token_current_jti="jti-abc", otp_code="hash")
        user.otp_failed_attempts = 3
        svc, repo = _make(user)

        result = svc.update(user_id=5, status=status, requester_user_id=1)

        assert result.success
        assert result.data.status == status
        saved = repo.update.call_args.args[0]
        assert saved.status == status
        assert saved.token_current_jti is None
        assert saved.otp_code is None
        assert saved.otp_expires_at is None
        assert saved.otp_failed_attempts == 0
        repo.commit.assert_called_once()

    def test_reactivating_keeps_no_session_and_writes(self):
        user = make_user(id=5, status="blocked")
        svc, repo = _make(user)

        result = svc.update(user_id=5, status="active", requester_user_id=1)

        assert result.data.status == "active"
        assert repo.update.call_args.args[0].status == "active"
        repo.commit.assert_called_once()

    def test_status_is_normalized(self):
        svc, repo = _make(make_user(id=5))

        result = svc.update(user_id=5, status="  BLOCKED ", requester_user_id=1)

        assert result.data.status == "blocked"

    def test_same_status_does_not_write(self):
        user = make_user(id=5, status="blocked", token_current_jti="jti-abc")
        svc, repo = _make(user)

        result = svc.update(user_id=5, status="blocked", requester_user_id=1)

        assert result.success
        repo.update.assert_not_called()
        repo.commit.assert_not_called()

    def test_cannot_change_own_status(self):
        svc, repo = _make(make_user(id=1))

        result = svc.update(user_id=1, status="blocked", requester_user_id=1)

        assert result.error.code == "USER_CANNOT_CHANGE_OWN_STATUS"
        assert result.error.http_status == 422
        repo.get_by_id.assert_not_called()

    def test_invalid_status(self):
        svc, repo = _make(make_user(id=5))

        result = svc.update(user_id=5, status="deleted", requester_user_id=1)

        assert result.error.code == "USER_INVALID_STATUS"
        assert result.error.http_status == 422
        repo.update.assert_not_called()

    def test_user_not_found(self):
        svc, repo = _make(None)

        result = svc.update(user_id=99, status="blocked", requester_user_id=1)

        assert result.error.code == "USER_NOT_FOUND"
        assert result.error.http_status == 404

    def test_rollback_when_update_fails(self):
        svc, repo = _make(make_user(id=5))
        repo.update.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError):
            svc.update(user_id=5, status="disabled", requester_user_id=1)

        repo.rollback.assert_called_once()
        repo.commit.assert_not_called()

    def test_payload_includes_role(self):
        svc, _ = _make(make_user(id=5, email="ana@x.com"))

        data = svc.update(user_id=5, status="blocked", requester_user_id=1).data

        assert data.email == "ana@x.com"
        assert data.role_code == "investor"
        assert data.role_name == "Inversor"


# ----------------------------------------------------------------------
# Pausa de agentes al bloquear / desactivar
# ----------------------------------------------------------------------

def _bot(bot_id: int, status: str):
    from app.modules.bots.domain.bot_entity import Bot

    bot = MagicMock(spec=Bot)
    bot.id = bot_id
    bot.status = status
    bot._ALLOWED_TRANSITIONS = Bot._ALLOWED_TRANSITIONS
    bot.can_transition_to.side_effect = lambda new: Bot.can_transition_to(bot, new)
    return bot


def _make_with_bots(user, bots):
    svc, repo = _make(user)
    account_repo = MagicMock()
    account_repo.list_by_user_id.return_value = [MagicMock(id=10), MagicMock(id=11)]
    bot_repo = MagicMock()
    bot_repo.list_by_account_ids.return_value = bots
    svc = UpdateUserStatusService(repo=repo, bot_repo=bot_repo, account_repo=account_repo)
    return svc, repo, bot_repo, account_repo


class TestPauseBotsOnDeactivation:

    @pytest.mark.parametrize("status", ["blocked", "disabled"])
    def test_pauses_only_running_bots_in_same_commit(self, status):
        running, stopped, paused = _bot(1, "running"), _bot(2, "stopped"), _bot(3, "paused")
        svc, repo, bot_repo, account_repo = _make_with_bots(
            make_user(id=5), [running, stopped, paused]
        )

        result = svc.update(user_id=5, status=status, requester_user_id=1)

        assert result.success
        account_repo.list_by_user_id.assert_called_once_with(5)
        bot_repo.list_by_account_ids.assert_called_once_with([10, 11])
        assert running.status == "paused"
        assert stopped.status == "stopped"
        assert paused.status == "paused"
        bot_repo.update.assert_called_once_with(running)
        repo.commit.assert_called_once()

    def test_reactivating_does_not_resume_bots(self):
        bot = _bot(1, "paused")
        svc, repo, bot_repo, account_repo = _make_with_bots(make_user(id=5, status="blocked"), [bot])

        svc.update(user_id=5, status="active", requester_user_id=1)

        assert bot.status == "paused"
        account_repo.list_by_user_id.assert_not_called()
        bot_repo.update.assert_not_called()

    def test_same_status_does_not_touch_bots(self):
        bot = _bot(1, "running")
        svc, repo, bot_repo, account_repo = _make_with_bots(make_user(id=5, status="blocked"), [bot])

        svc.update(user_id=5, status="blocked", requester_user_id=1)

        assert bot.status == "running"
        bot_repo.update.assert_not_called()

    def test_failure_pausing_rolls_back(self):
        bot = _bot(1, "running")
        svc, repo, bot_repo, _ = _make_with_bots(make_user(id=5), [bot])
        bot_repo.update.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError):
            svc.update(user_id=5, status="blocked", requester_user_id=1)

        repo.rollback.assert_called_once()
        repo.commit.assert_not_called()
