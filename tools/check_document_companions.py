"""Verify original exam hashes, attachment declarations and runnable source paths."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def file_path(name):
    path = (ROOT / name).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), "Missing/unsafe path: " + name)
    return path


def main():
    manifest = json.loads((ROOT / "document-companions.json").read_text(encoding="utf-8"))
    require(manifest["schema_version"] == 1, "Unsupported manifest schema")
    require({row["year"] for row in manifest["exams"]} == {2008, 2009, 2022, 2023, 2024}, "Expected five exam sets")
    gaps = []
    for exam in manifest["exams"]:
        document = exam["original_document"]
        if "path" in document:
            path = file_path(document["path"])
            require(hashlib.sha256(path.read_bytes()).hexdigest() == document["sha256"], "Original PDF hash differs")
            for reference in exam["file_references"]:
                require(1 <= reference["page"] <= document["pages"], "Reference page is outside document")
                require(reference["status"] in ("not_provided", "student_submission_requirement"), "Unresolved reference")
        else:
            require(document["status"] == "original_source_unavailable", "Unexplained original PDF omission")
            require(document["reason"] and document["source_filename"], "Missing original PDF availability evidence")
            file_path(document["transcription"])
        transcription = exam["question_transcription"]
        require(hashlib.sha256(file_path(transcription["path"]).read_bytes()).hexdigest() == transcription["sha256"], "Question transcription hash differs")
        for name in exam["implemented_sources"]:
            file_path(name)
        for companion in exam["original_companions"]:
            require(companion["status"] == "not_provided", "Unexplained original companion status")
            reference = companion["instruction_reference"]
            require(reference["document"] == document["path"] and reference["page"] == 1, "Invalid missing-template evidence")
            require(companion["limitation"] and companion["search_scope"], "Missing gap scope/limitation")
            gaps.append(companion)
        if "generated_simulation_inputs" in exam:
            generated = exam["generated_simulation_inputs"]
            require(generated["role"] == "repository_generated_test_stimulus_not_original_attachment", "Generated vectors mislabelled as originals")
            file_path(generated["generator"])
            require(len(generated["files"]) == 8, "Incomplete 2023 stimulus inventory")
    require(gaps == manifest["unavailable"], "Missing-template inventory differs")
    require([(row["year"], row["name"]) for row in gaps] == [(2023, "DSD.v"), (2024, "DSD.v")], "Expected explicit declarations of both missing original templates")
    preservation = manifest["preservation_review"]
    require(preservation["original_materials_complete"] is False, "Unavailable originals cannot be labelled complete")
    require(preservation["unavailable_original_documents"] == [{"year": 2008, "name": "Final-Exam-2008-Answer.pdf"}], "Missing 2008 original scan declaration")
    require(preservation["unavailable_original_companions"] == [{"year": row["year"], "name": row["name"]} for row in gaps], "Preservation gap inventory differs")
    print("PASS original integrity: four original PDFs, five question transcriptions and all runnable source paths.")
    print("NOT AVAILABLE: 2008 / Final-Exam-2008-Answer.pdf (original scan)")
    for row in gaps:
        print("NOT PROVIDED: " + str(row["year"]) + " / " + row["name"] + " (original instructor template)")


if __name__ == "__main__":
    main()
