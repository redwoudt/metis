from metis.examples.chapter14_memory import main


def test_chapter14_example_reports_sharing_restoration_and_eviction(capsys) -> None:
    main()

    output = capsys.readouterr().out.splitlines()

    assert "Logical artifact references : 15" in output
    assert "Unique stored artifacts     : 6" in output
    assert "Reference reuse ratio       : 2.50x" in output
    assert "Observable state restored   : True" in output
    assert "Eviction while referenced   : blocked" in output
    assert "Eviction after release      : allowed" in output

