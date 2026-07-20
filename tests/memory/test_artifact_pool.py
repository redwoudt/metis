import pytest

from metis.memory import ArtifactPool, MissingArtifactError


def test_pool_reuses_canonical_artifact_within_tenant_and_version():
    pool = ArtifactPool()

    first = pool.intern(
        tenant_id="tenant-a",
        artifact_type="system-prompt",
        version="v1",
        content={"role": "helpful"},
    )
    second = pool.intern(
        tenant_id="tenant-a",
        artifact_type="system-prompt",
        version="v1",
        content={"role": "helpful"},
    )

    assert first == second
    assert pool.get(first) is pool.get(second)
    assert len(pool) == 1


def test_pool_keys_prevent_cross_tenant_and_cross_version_reuse():
    pool = ArtifactPool()
    common = {"role": "helpful"}

    tenant_a_v1 = pool.intern(
        tenant_id="tenant-a",
        artifact_type="system-prompt",
        version="v1",
        content=common,
    )
    tenant_b_v1 = pool.intern(
        tenant_id="tenant-b",
        artifact_type="system-prompt",
        version="v1",
        content=common,
    )
    tenant_a_v2 = pool.intern(
        tenant_id="tenant-a",
        artifact_type="system-prompt",
        version="v2",
        content=common,
    )

    assert len({tenant_a_v1, tenant_b_v1, tenant_a_v2}) == 3
    assert len(pool) == 3


def test_resolved_values_cannot_mutate_the_shared_artifact():
    pool = ArtifactPool()
    reference = pool.intern(
        tenant_id="tenant-a",
        artifact_type="tool-schema",
        version="v1",
        content={"tools": ["search"]},
    )

    resolved = pool.resolve(reference)
    resolved["tools"].append("delete")

    assert pool.resolve(reference) == {"tools": ["search"]}


def test_pinned_artifact_resists_eviction_until_released():
    pool = ArtifactPool()
    reference = pool.intern(
        tenant_id="tenant-a",
        artifact_type="safety-policy",
        version="v1",
        content={"blocked": ["secret"]},
    )

    pool.retain([reference])
    assert pool.evict(reference) is False

    pool.release([reference])
    assert pool.evict(reference) is True
    with pytest.raises(MissingArtifactError, match="Cannot restore"):
        pool.resolve(reference)
