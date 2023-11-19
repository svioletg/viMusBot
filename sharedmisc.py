def get_nested(check: dict, default: dict, *key_path):
	for key in key_path:
		if isinstance(check, dict) and key in check:
			check = check[key]
			default = default[key]
		else:
			return default[key]
	return check