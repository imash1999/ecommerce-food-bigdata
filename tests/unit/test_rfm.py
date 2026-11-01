def assign_segment(r_score: int, f_score: int) -> str:
    if r_score >= 4 and f_score >= 4:
        return "Champions"
    if r_score >= 3 and f_score >= 3:
        return "Loyal Customers"
    if r_score >= 3 and f_score < 3:
        return "Promising / Recent"
    if r_score < 3 and f_score >= 3:
        return "At Risk"
    return "Lost / Hibernating"


class TestRFMSegmentation:
    def test_champions(self):
        assert assign_segment(5, 5) == "Champions"
        assert assign_segment(4, 4) == "Champions"

    def test_loyal_customers(self):
        assert assign_segment(3, 3) == "Loyal Customers"
        assert assign_segment(4, 3) == "Loyal Customers"
        assert assign_segment(3, 4) == "Loyal Customers"

    def test_promising_recent(self):
        assert assign_segment(3, 2) == "Promising / Recent"
        assert assign_segment(5, 1) == "Promising / Recent"

    def test_at_risk(self):
        assert assign_segment(2, 3) == "At Risk"
        assert assign_segment(1, 5) == "At Risk"

    def test_lost_hibernating(self):
        assert assign_segment(1, 1) == "Lost / Hibernating"
        assert assign_segment(2, 2) == "Lost / Hibernating"

    def test_all_combinations_covered(self):
        segments = set()
        for r in range(1, 6):
            for f in range(1, 6):
                segments.add(assign_segment(r, f))
        assert len(segments) == 5

    def test_segment_names(self):
        expected = {
            "Champions", "Loyal Customers", "Promising / Recent",
            "At Risk", "Lost / Hibernating",
        }
        actual = set()
        for r in range(1, 6):
            for f in range(1, 6):
                actual.add(assign_segment(r, f))
        assert actual == expected