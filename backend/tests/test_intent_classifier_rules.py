import unittest

from agentic_ai.chatbot.agents.intent_classifier import _is_company_profile_query


class IntentClassifierRuleTests(unittest.TestCase):
    def test_company_profile_questions_with_ticker_are_market_queries(self):
        questions = (
            "FPT hoạt động trong ngành nào?",
            "MWG kinh doanh gì?",
            "Hồ sơ doanh nghiệp VNM",
            "Ban lãnh đạo HPG gồm những ai?",
            "VIC niêm yết ở sàn nào?",
            "What industry does FPT operate in?",
        )
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(_is_company_profile_query(question))

    def test_questions_without_ticker_do_not_match_the_deterministic_rule(self):
        self.assertFalse(_is_company_profile_query("Ngành ngân hàng gồm những gì?"))
        self.assertFalse(_is_company_profile_query("Công ty hoạt động trong ngành nào?"))


if __name__ == "__main__":
    unittest.main()
