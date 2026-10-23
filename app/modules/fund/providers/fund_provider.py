# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/providers/fund_provider.py
#
# Factory de los servicios del fondo común (F3: ajustes, libro mayor y
# depósitos). Reutiliza de M4 la billetera de la plataforma, sus cuentas y
# el gateway del exchange; de M1, el repositorio de usuarios.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.security.credentials_cipher import CredentialsCipher
from app.modules.accounts.infrastructure import (
    SqlAlchemyAccountRepository,
    SqlAlchemyPlatformWalletRepository,
)
from app.modules.accounts.infrastructure.ccxt_wallet_gateway import CcxtWalletGateway
from app.modules.bots.infrastructure import SqlAlchemyBotRepository
from app.modules.fund.infrastructure import (
    SqlAlchemyCommissionCreditRepository,
    SqlAlchemyCommissionShareRepository,
    SqlAlchemyFeeScheduleRepository,
    SqlAlchemyPayoutMethodRepository,
    SqlAlchemyRedemptionRequestRepository,
    SqlAlchemySettlementRedemptionRepository,
    SqlAlchemyWithdrawalRequestRepository,
    SqlAlchemyAgentPoolRepository,
    SqlAlchemyAgentSettlementRepository,
    SqlAlchemyAllocationOrderRepository,
    SqlAlchemyDepositRequestRepository,
    SqlAlchemyUnitLotRepository,
    SqlAlchemyFundSettingsRepository,
    SqlAlchemyLedgerRepository,
)
from app.modules.fund.services.deposits import (
    CreateDepositRequestService,
    ResolveDepositRequestService,
    UnclaimedDepositsService,
    VerifyDepositsService,
)
from app.modules.fund.services.fees import CommissionSharesService, FeeScheduleService
from app.modules.fund.services.ledger import FundLedgerService
from app.modules.fund.services.payouts import PayoutMethodsService, WithdrawalService
from app.modules.fund.services.pools import (
    AgentCapitalService,
    AgentInfoReader,
    AgentPoolsService,
    AllocationService,
    ParticipationsService,
    RedemptionService,
    SettleAgentService,
)
from app.modules.fund.services.settings import DepositNetworksService, FundSettingsService
from app.modules.fund.services.wallet_context import WalletContextResolver
from app.modules.market.infrastructure import (
    SqlAlchemyExchangeRepository,
    SqlAlchemySymbolRepository,
)
from app.modules.orders.infrastructure import (
    SqlAlchemyFillRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyPositionRepository,
)
from app.modules.users.infrastructure import SqlAlchemyUserRepository


class FundServiceFactory:
    """Todos los repos comparten la sesión: un commit confirma todo el caso de uso."""

    def __init__(self, session: Session):
        self._session = session
        self._settings_repo = SqlAlchemyFundSettingsRepository(session)
        self._ledger_repo = SqlAlchemyLedgerRepository(session)
        self._deposit_repo = SqlAlchemyDepositRequestRepository(session)
        self._user_repo = SqlAlchemyUserRepository(session)
        self._wallet_repo = SqlAlchemyPlatformWalletRepository(session)
        self._wallet_resolver = WalletContextResolver(
            wallet_repo=self._wallet_repo,
            account_repo=SqlAlchemyAccountRepository(session),
        )
        # F4: capital de los agentes
        self._pool_repo = SqlAlchemyAgentPoolRepository(session)
        self._settlement_repo = SqlAlchemyAgentSettlementRepository(session)
        self._lot_repo = SqlAlchemyUnitLotRepository(session)
        self._allocation_repo = SqlAlchemyAllocationOrderRepository(session)
        self._bot_repo = SqlAlchemyBotRepository(session)
        self._symbol_repo = SqlAlchemySymbolRepository(session)
        self._fill_repo = SqlAlchemyFillRepository(session)
        # F5: salidas, comisiones y retiros
        self._redemption_repo = SqlAlchemyRedemptionRequestRepository(session)
        self._line_repo = SqlAlchemySettlementRedemptionRepository(session)
        self._credit_repo = SqlAlchemyCommissionCreditRepository(session)
        self._fee_repo = SqlAlchemyFeeScheduleRepository(session)
        self._shares_repo = SqlAlchemyCommissionShareRepository(session)
        self._payout_repo = SqlAlchemyPayoutMethodRepository(session)
        self._withdrawal_repo = SqlAlchemyWithdrawalRequestRepository(session)

    def _gateway(self) -> CcxtWalletGateway:
        # Solo se arma cuando el caso de uso habla con el exchange
        return CcxtWalletGateway(
            exchange_repo=SqlAlchemyExchangeRepository(self._session),
            cipher=CredentialsCipher.from_settings(),
        )

    # ------------------------------------------------------------------
    # Ajustes
    # ------------------------------------------------------------------

    def fund_settings(self) -> FundSettingsService:
        return FundSettingsService(
            settings_repo=self._settings_repo, wallet_resolver=self._wallet_resolver
        )

    def deposit_networks(self) -> DepositNetworksService:
        return DepositNetworksService(
            settings_repo=self._settings_repo,
            wallet_resolver=self._wallet_resolver,
            gateway=self._gateway(),
        )

    # ------------------------------------------------------------------
    # Depósitos
    # ------------------------------------------------------------------

    def create_deposit_request(self) -> CreateDepositRequestService:
        return CreateDepositRequestService(
            deposit_repo=self._deposit_repo,
            settings_repo=self._settings_repo,
            wallet_resolver=self._wallet_resolver,
        )

    def resolve_deposit_request(self) -> ResolveDepositRequestService:
        return ResolveDepositRequestService(
            deposit_repo=self._deposit_repo, ledger_repo=self._ledger_repo
        )

    def verify_deposits(self) -> VerifyDepositsService:
        return VerifyDepositsService(
            deposit_repo=self._deposit_repo,
            ledger_repo=self._ledger_repo,
            settings_repo=self._settings_repo,
            wallet_resolver=self._wallet_resolver,
            gateway=self._gateway(),
        )

    def unclaimed_deposits(self) -> UnclaimedDepositsService:
        return UnclaimedDepositsService(
            deposit_repo=self._deposit_repo,
            ledger_repo=self._ledger_repo,
            user_repo=self._user_repo,
            wallet_resolver=self._wallet_resolver,
            gateway=self._gateway(),
        )

    # ------------------------------------------------------------------
    # Libro mayor
    # ------------------------------------------------------------------

    def ledger(self) -> FundLedgerService:
        return FundLedgerService(
            ledger_repo=self._ledger_repo,
            user_repo=self._user_repo,
            asset=settings.WALLET_BASE_ASSET,
        )

    # ------------------------------------------------------------------
    # Capital de los agentes (F4)
    # ------------------------------------------------------------------

    def agent_capital(self) -> AgentCapitalService:
        return AgentCapitalService(
            pool_repo=self._pool_repo,
            wallet_repo=self._wallet_repo,
            fill_repo=self._fill_repo,
            position_repo=SqlAlchemyPositionRepository(self._session),
            symbol_repo=self._symbol_repo,
        )

    def agent_pools(self) -> AgentPoolsService:
        return AgentPoolsService(
            pool_repo=self._pool_repo,
            lot_repo=self._lot_repo,
            allocation_repo=self._allocation_repo,
            settlement_repo=self._settlement_repo,
            wallet_repo=self._wallet_repo,
            bot_repo=self._bot_repo,
            symbol_repo=self._symbol_repo,
            fill_repo=self._fill_repo,
            capital=self.agent_capital(),
            redemption_repo=self._redemption_repo,
        )

    def allocations(self) -> AllocationService:
        return AllocationService(
            allocation_repo=self._allocation_repo,
            pool_repo=self._pool_repo,
            ledger_repo=self._ledger_repo,
            user_repo=self._user_repo,
            withdrawal_repo=self._withdrawal_repo,
        )

    def settle_agent(self) -> SettleAgentService:
        return SettleAgentService(
            pool_repo=self._pool_repo,
            settlement_repo=self._settlement_repo,
            lot_repo=self._lot_repo,
            allocation_repo=self._allocation_repo,
            ledger_repo=self._ledger_repo,
            bot_repo=self._bot_repo,
            order_repo=SqlAlchemyOrderRepository(self._session),
            capital=self.agent_capital(),
            settings_repo=self._settings_repo,
            redemption_repo=self._redemption_repo,
            line_repo=self._line_repo,
            credit_repo=self._credit_repo,
            fee_repo=self._fee_repo,
            shares_repo=self._shares_repo,
        )

    def participations(self) -> ParticipationsService:
        return ParticipationsService(
            lot_repo=self._lot_repo,
            pool_repo=self._pool_repo,
            settlement_repo=self._settlement_repo,
            agents=AgentInfoReader(self._bot_repo, self._symbol_repo),
        )


    # ------------------------------------------------------------------
    # Salidas, comisiones y retiros (F5)
    # ------------------------------------------------------------------

    def redemptions(self) -> RedemptionService:
        return RedemptionService(
            repo=self._redemption_repo,
            line_repo=self._line_repo,
            pool_repo=self._pool_repo,
            lot_repo=self._lot_repo,
            agents=AgentInfoReader(self._bot_repo, self._symbol_repo),
        )

    def fee_schedule(self) -> FeeScheduleService:
        return FeeScheduleService(repo=self._fee_repo)

    def commission_shares(self) -> CommissionSharesService:
        return CommissionSharesService(
            repo=self._shares_repo,
            credit_repo=self._credit_repo,
            user_repo=self._user_repo,
            # Reciben comisión los propietarios: super admin y socios
            owner_role_ids=frozenset(
                {settings.AUTH_SUPER_ADMIN_ROLE_ID, settings.AUTH_PARTNER_ROLE_ID}
            ),
        )

    def payout_methods(self) -> PayoutMethodsService:
        return PayoutMethodsService(
            repo=self._payout_repo,
            cipher=CredentialsCipher.from_settings(),
            cooldown_hours=settings.PAYOUT_METHOD_COOLDOWN_HOURS,
        )

    def withdrawals(self) -> WithdrawalService:
        return WithdrawalService(
            repo=self._withdrawal_repo,
            payout_repo=self._payout_repo,
            ledger_repo=self._ledger_repo,
            allocation_repo=self._allocation_repo,
            asset=settings.WALLET_BASE_ASSET,
        )


def build_fund_capital(session: Session) -> AgentCapitalService:
    """
    Capital de los agentes del fondo para bots y orders (FundCapitalPort).
    Función aparte para que esos módulos no construyan la factory completa.
    """
    return FundServiceFactory(session).agent_capital()

