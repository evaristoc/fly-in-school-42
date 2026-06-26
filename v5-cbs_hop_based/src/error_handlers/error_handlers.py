class ConfigError(Exception):
    pass


class DuplicatesError(ConfigError):
    pass


class InvalidEntryError(ConfigError):
    pass
