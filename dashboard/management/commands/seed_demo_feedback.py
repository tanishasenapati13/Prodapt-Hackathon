"""
Management command: seed_demo_feedback

Seeds a few rounds of fake recruiter feedback to demonstrate the
Feedback Loop feature during a live demo.

Usage:
    python manage.py seed_demo_feedback
    python manage.py seed_demo_feedback --reset   # clear existing feedback first
"""

from django.core.management.base import BaseCommand

from dashboard.models import MatchFeedback, SkillWeightSnapshot
from dashboard.services.skill_weights import record_feedback


# Demo feedback scenarios
DEMO_FEEDBACK = [
    # Round 1: Recruiter likes Python + SQL candidates
    {"match_id": "res_001", "feedback": "good_fit", "skills": ["python", "sql", "fastapi", "docker"]},
    {"match_id": "res_002", "feedback": "good_fit", "skills": ["python", "sql", "docker"]},
    # Round 2: Recruiter dislikes candidate with few skills
    {"match_id": "res_003", "feedback": "not_a_fit", "skills": ["python", "sql"]},
    # Round 3: More emphasis on python and fastapi
    {"match_id": "res_001", "feedback": "good_fit", "skills": ["python", "sql", "fastapi", "docker"]},
    {"match_id": "res_001", "feedback": "good_fit", "skills": ["python", "sql", "fastapi", "docker"]},
    # Round 4: Docker gets a negative signal
    {"match_id": "res_003", "feedback": "not_a_fit", "skills": ["python", "sql"]},
]


class Command(BaseCommand):
    help = "Seed demo feedback to showcase the Feedback Loop re-ranking feature."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Clear all existing feedback and skill weights before seeding.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            count_fb = MatchFeedback.objects.all().delete()[0]
            count_sw = SkillWeightSnapshot.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(
                    f"Cleared {count_fb} feedback rows and {count_sw} weight snapshots."
                )
            )

        self.stdout.write("Seeding demo feedback...")

        for i, fb in enumerate(DEMO_FEEDBACK, 1):
            record_feedback(
                match_id=fb["match_id"],
                recruiter_id=0,
                feedback=fb["feedback"],
                skill_snapshot=fb["skills"],
            )
            emoji = "👍" if fb["feedback"] == "good_fit" else "👎"
            self.stdout.write(
                f"  {i}. {emoji} {fb['feedback']} for {fb['match_id']} "
                f"({', '.join(fb['skills'])})"
            )

        # Show resulting weights
        snapshot = SkillWeightSnapshot.objects.first()
        weights = snapshot.weights if snapshot else {}
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Resulting skill weights:"))
        for skill, weight in sorted(weights.items()):
            bar = "█" * int(weight * 10)
            self.stdout.write(f"  {skill:12s} → {weight:.2f}  {bar}")

        total = MatchFeedback.objects.count()
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done! {len(DEMO_FEEDBACK)} feedback events seeded "
                f"({total} total in DB). Refresh the dashboard to see re-ranking."
            )
        )
