"""Tests for generate_matrix.py."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from generate_matrix import ServiceConfig, build_matrix, extract


class TestExtract:
    def test_double_quoted(self):
        assert extract('repo: "my-repo"', "repo") == "my-repo"

    def test_single_quoted(self):
        assert extract("repo: 'my-repo'", "repo") == "my-repo"

    def test_unquoted(self):
        assert extract("repo: my-repo", "repo") == "my-repo"

    def test_missing_field_returns_none(self):
        assert extract("other: value", "repo") is None

    def test_indented_field(self):
        content = "  service: my-service\n"
        assert extract(content, "service") == "my-service"


class TestBuildMatrix:
    def test_empty_dir_returns_empty_list(self, tmp_path):
        assert build_matrix(str(tmp_path)) == []

    def test_file_without_repo_is_skipped(self, tmp_path):
        (tmp_path / "svc-framework.yml").write_text("service: only-service\n")
        assert build_matrix(str(tmp_path)) == []

    def test_file_without_service_is_skipped(self, tmp_path):
        (tmp_path / "svc-framework.yml").write_text("repo: only-repo\n")
        assert build_matrix(str(tmp_path)) == []

    def test_single_service_parsed_correctly(self, tmp_path):
        (tmp_path / "my-service-framework.yml").write_text(
            'repo: "my-repo"\nservice: "my-service"\n'
        )
        result = build_matrix(str(tmp_path))
        assert len(result) == 1
        entry = result[0]
        assert isinstance(entry, ServiceConfig)
        assert entry.repo == "my-repo"
        assert entry.service == "my-service"
        assert entry.config == "my-service-framework.yml"
        assert entry.build_go is False
        assert entry.service_package == "my-repo"
        assert entry.binary_repo == ""
        assert entry.profile == ""

    def test_go_service_has_empty_service_package(self, tmp_path):
        (tmp_path / "go-svc-framework.yml").write_text(
            'repo: "go-repo"\nservice: "go-svc"\nbuild_go: "true"\n'
        )
        result = build_matrix(str(tmp_path))
        assert len(result) == 1
        entry = result[0]
        assert entry.build_go is True
        assert entry.service_package == ""

    def test_binary_repo_and_profile_are_captured(self, tmp_path):
        (tmp_path / "full-framework.yml").write_text(
            "repo: r\nservice: s\nbinary_repo: b-repo\ndocker_profile: my-profile\n"
        )
        result = build_matrix(str(tmp_path))
        assert result[0].binary_repo == "b-repo"
        assert result[0].profile == "my-profile"

    def test_multiple_services(self, tmp_path):
        for i in range(3):
            (tmp_path / f"svc{i}-framework.yml").write_text(f"repo: repo{i}\nservice: svc{i}\n")
        result = build_matrix(str(tmp_path))
        assert len(result) == 3

    def test_non_framework_files_are_ignored(self, tmp_path):
        (tmp_path / "other.yml").write_text("repo: r\nservice: s\n")
        assert build_matrix(str(tmp_path)) == []
