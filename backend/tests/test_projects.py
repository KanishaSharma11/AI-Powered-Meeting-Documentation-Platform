def test_create_project(client):
    res = client.post("/api/projects", json={"name": "Acme SRS", "description": "Acme requirements project"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["name"] == "Acme SRS"
    assert body["meeting_count"] == 0


def test_create_project_requires_name(client):
    res = client.post("/api/projects", json={"name": "   "})
    assert res.status_code == 400


def test_list_projects_includes_created(client, project):
    res = client.get("/api/projects")
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert project["id"] in ids


def test_get_project_by_id(client, project):
    res = client.get(f"/api/projects/{project['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == project["id"]


def test_get_unknown_project_returns_404(client):
    res = client.get("/api/projects/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


def test_upload_with_unknown_project_id_returns_404(client):
    res = client.post(
        "/api/transcripts/upload",
        json={
            "title": "Orphan meeting",
            "raw_transcript": "Sarah: Hello.",
            "project_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert res.status_code == 404


def test_meeting_linked_to_project_reflects_in_meeting_count(client, project, meeting_in_project):
    res = client.get(f"/api/projects/{project['id']}")
    assert res.json()["meeting_count"] == 1


def test_standalone_meeting_has_null_project_id(client, meeting_with_segments):
    meeting_id, _ = meeting_with_segments
    res = client.get("/api/transcripts")
    meeting = next(m for m in res.json() if m["id"] == meeting_id)
    assert meeting["project_id"] is None