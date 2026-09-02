from tests.conftest import register


def test_rule_version_increments_and_old_identity_is_preserved(client):
    register(client, "rules@example.com")
    created = client.post(
        "/api/rules",
        json={
            "rule_type": "max_position_pct",
            "name": "Max position",
            "severity": "HARD",
            "threshold": "20",
        },
    )
    rule = created.json()["rule"]
    assert rule["version"] == 1
    updated = client.patch(f"/api/rules/{rule['id']}", json={"threshold": "15"})
    assert updated.status_code == 200
    body = updated.json()["rule"]
    assert body["threshold"] == "15"
    assert body["version"] == 2
