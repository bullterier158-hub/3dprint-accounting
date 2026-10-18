# ui/common.py

def parse_float(text: str, default: float | None = None) -> float:
    """Преобразует '1,5' в 1.5. Возвращает default если пусто, бросает ValueError если мусор."""
    s = (text or "").strip().replace(",", ".")
    if not s:
        if default is not None:
            return default
        raise ValueError("Пустое значение")
    return float(s)

def fmt_float(val, precision=2) -> str:
    """Форматирует число с заданной точностью, заменяя точку на запятую."""
    if val is None:
        return ""
    return f"{val:.{precision}f}".replace(".", ",")