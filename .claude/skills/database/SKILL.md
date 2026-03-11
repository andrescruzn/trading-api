---
name: database
description: Database conventions for this project (MySQL 8 via MAMP). Use before writing migrations, seeds, or raw SQL queries. Covers MySQL CLI commands, connection credentials, seed conventions, table naming rules, and SQLAlchemy-specific gotchas.
---

# Skill: Database — MySQL con MAMP

## Motor MySQL en este proyecto

El proyecto usa **MAMP** como servidor MySQL local.
El binario `mysql` NO está en el PATH del sistema — hay que usar la ruta completa.

---

## Comandos MySQL

### Ejecutar un archivo SQL (seed, migración, etc.)

```bash
/Applications/MAMP/Library/bin/mysql80/bin/mysql -u root -proot trading_ai < ruta/al/archivo.sql
```

### Conectarse al shell interactivo

```bash
/Applications/MAMP/Library/bin/mysql80/bin/mysql -u root -proot trading_ai
```

### Ejecutar una query directa

```bash
/Applications/MAMP/Library/bin/mysql80/bin/mysql -u root -proot trading_ai -e "SELECT COUNT(*) FROM candles;"
```

---

## Credenciales locales

| Campo    | Valor       |
|----------|-------------|
| Usuario  | `root`      |
| Password | `root`      |
| Base de datos | `trading_ai` |
| Host     | `127.0.0.1` |
| Puerto   | `3306` (MAMP default) |

> ⚠️ El warning `Using a password on the command line interface can be insecure` es normal y esperado — no es un error.

---

## Seeds disponibles

| Archivo | Qué inserta |
|---------|------------|
| `seeds/seed_market_data.sql` | exchanges, timeframes, symbols (M2) |

### Crear un nuevo seed

- Poner el archivo en `seeds/seed_<modulo>.sql`
- Siempre usar `INSERT IGNORE` o `INSERT ... ON DUPLICATE KEY UPDATE` para que sea **idempotente**
- Usar subqueries para referencias por nombre en vez de hardcodear IDs:
  ```sql
  SELECT id FROM exchanges WHERE name = 'Binance'
  ```
- Terminar con un `SELECT COUNT(*)` de verificación

---

## Convenciones de tablas (resumen)

- IDs: `BIGINT AUTO_INCREMENT` (excepto `timeframes.id` que es `SMALLINT`)
- Timestamps: `TIMESTAMP(6)` siempre
- Precios/cantidades financieras: `DECIMAL(30,12)`
- Datos flexibles: columnas `JSON` con CHECK `json_valid()`
- Charset: `utf8mb4`, collation: `utf8mb4_0900_ai_ci`
- Motor: `InnoDB`
- En SQLAlchemy Core usar `sqlalchemy.dialects.mysql.TIMESTAMP(fsp=6)` — NO el genérico `TIMESTAMP(6)`
