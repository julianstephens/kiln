def test_generated_schema_package_imports() -> None:
    import kiln.schemas as schemas

    assert schemas.event.EventEnvelope is not None
    assert schemas.run.RunSpecification is not None
    assert schemas.model.ModelGeneratePayload is not None
    assert schemas.repository.RepositoryOpenSessionRequestPayload is not None
