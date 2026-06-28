def test_generated_schema_package_imports() -> None:
    import kiln.schemas as schemas

    assert schemas.EventEnvelope is not None
    assert schemas.RunSpecification is not None
    assert schemas.ModelGenerateRequest is not None
    assert schemas.RepositoryOpenSessionRequest is not None
