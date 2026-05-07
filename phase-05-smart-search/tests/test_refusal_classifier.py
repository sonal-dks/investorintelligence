"""Tests for RefusalClassifier — covers advice patterns and factual pass-through."""

import pytest

from backend.services.refusal_classifier import RefusalClassifier


@pytest.fixture
def classifier():
    return RefusalClassifier()


class TestAdviceRefusal:
    def test_should_i_invest(self, classifier: RefusalClassifier):
        should_refuse, reason = classifier.check("Should I invest in this fund?")
        assert should_refuse is True
        assert reason is not None
        assert "investment advice" in reason.lower() or "recommend" in reason.lower()

    def test_recommend_fund(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("Can you recommend a good fund?")
        assert should_refuse is True

    def test_which_fund_is_better(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("Which fund is better for me?")
        assert should_refuse is True

    def test_buy_or_sell(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("Should I buy or sell ELSS now?")
        assert should_refuse is True

    def test_will_it_go_up(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("Will the NAV go up next month?")
        assert should_refuse is True

    def test_prediction(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("What is your prediction for large cap?")
        assert should_refuse is True

    def test_best_fund(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("What is the best fund to invest in?")
        assert should_refuse is True

    def test_guarantee(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("Can you guarantee returns?")
        assert should_refuse is True


class TestFactualPassthrough:
    def test_exit_load_question(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("What is the exit load of Mirae Asset Large Cap?")
        assert should_refuse is False

    def test_nav_question(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("What is the current NAV?")
        assert should_refuse is False

    def test_expense_ratio_question(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("What is the expense ratio of Flexi Cap fund?")
        assert should_refuse is False

    def test_sip_question(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("What is the minimum SIP for ELSS?")
        assert should_refuse is False

    def test_empty_string(self, classifier: RefusalClassifier):
        should_refuse, _ = classifier.check("")
        assert should_refuse is False
