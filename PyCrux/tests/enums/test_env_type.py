from pycrux.enums import EnvType


def test_canonical_values() -> None:
    assert EnvType.LOCAL.value == "local"
    assert EnvType.DEV.value == "dev"
    assert EnvType.PROD.value == "prod"
    assert EnvType.QA.value == "qa"
    assert EnvType.STAGING.value == "stg"
    assert EnvType.TEST.value == "test"
    assert EnvType.UAT.value == "uat"


def test_from_string_accepts_key_alias_and_name() -> None:
    assert EnvType.from_string("stg") is EnvType.STAGING
    assert EnvType.from_string("staging") is EnvType.STAGING
    assert EnvType.from_string("STAGING") is EnvType.STAGING
    assert EnvType.from_string(" Development ") is EnvType.DEV
    assert EnvType.from_string("live") is EnvType.PROD
    assert EnvType.from_string(EnvType.QA) is EnvType.QA


def test_from_string_rejects_invalid() -> None:
    assert EnvType.from_string("") is None
    assert EnvType.from_string("   ") is None
    assert EnvType.from_string(None) is None
    assert EnvType.from_string("preprod") is None


def test_equals_and_not_equals() -> None:
    assert EnvType.STAGING.equals("stg")
    assert EnvType.STAGING.equals("STAGE")
    assert EnvType.STAGING.equals(EnvType.STAGING)
    assert not EnvType.STAGING.equals("prod")
    assert not EnvType.STAGING.equals("")
    assert EnvType.STAGING.not_equals("prod")
    assert not EnvType.STAGING.not_equals("staging")


def test_equals_any_and_not_equals_any() -> None:
    assert EnvType.PROD.equals_any(["staging", "production"])
    assert EnvType.PROD.equals_any([EnvType.QA, EnvType.PROD])
    assert not EnvType.PROD.equals_any(["qa", "dev"])
    assert EnvType.DEV.not_equals_any(["prod", "staging"])
    assert not EnvType.DEV.not_equals_any(["dev", "prod"])


def test_env_type_and_aliases() -> None:
    assert EnvType.STAGING.env_type == "stg"
    assert "staging" in EnvType.STAGING.aliases
    assert str(EnvType.STAGING) == "stg"


def test_names() -> None:
    assert EnvType.names() == [
        "LOCAL",
        "DEV",
        "PROD",
        "QA",
        "STAGING",
        "TEST",
        "UAT",
    ]
