def generate_layout_id(generation_id: str, parameters: dict) -> str:
    parts = [generation_id]

    for key in sorted(parameters.keys()):
        value = parameters[key]

        if isinstance(value, bool):
            value_str = "true" if value else "false"
        elif isinstance(value, float):
            value_str = f"{value:.2f}".replace('.', 'p')
        elif isinstance(value, int):
            value_str = str(value)
        else:
            value_str = str(value).replace('.', 'p')  # fallback: ensure dot-free

        parts.append(f"{key}_{value_str}")

    return "_".join(parts)