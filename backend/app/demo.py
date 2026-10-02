"""An idempotent, local repository of fictional community issues for the demo."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.store import Base, Repository, Task, engine

DEMO_PATH = "community-care/civic-issues"
DEMO_NAME = "Community Care / Civic Issues"

# These are presentation examples, not reports of actual incidents or requests.
ISSUES = [
    (
        "Help serve dinner at the neighborhood soup kitchen",
        "Prepare serving stations, portion meals, and welcome guests during the evening meal. A shift lead provides an orientation and assigns kitchen duties.",
        "Food security",
        ["food preparation", "communication"],
        "Beginner",
        3,
        "Riverside Community Kitchen",
        "Community Meals Team",
    ),
    (
        "Coordinate pothole filling on Oak Street",
        "Document the damaged road surface and coordinate the repair request with the public works team. Any filling is performed by the authorized road crew; volunteers help with reporting and resident updates.",
        "Transportation",
        ["coordination", "documentation"],
        "Intermediate",
        2,
        "Oak Street near the community center",
        "Neighborhood Streets Team",
    ),
    (
        "Pack food pantry boxes for local families",
        "Sort shelf-stable donations and pack balanced grocery boxes. Follow the pantry checklist and flag damaged packaging to the shift lead.",
        "Food security",
        ["organization", "teamwork"],
        "Beginner",
        2,
        "Westside Food Pantry",
        "Food Pantry Volunteers",
    ),
    (
        "Clean up litter along the river trail",
        "Join a small team to collect litter along the walking trail. Bags and gloves are supplied at the meeting point; a coordinator handles disposal.",
        "Environment",
        ["teamwork"],
        "Beginner",
        2,
        "Riverside Trail entrance",
        "River Friends",
    ),
    (
        "Plant vegetables in the community garden",
        "Help prepare planting beds and plant seasonal vegetables for the shared harvest. A garden lead will explain spacing and watering.",
        "Environment",
        ["gardening", "teamwork"],
        "Beginner",
        4,
        "Maple Community Garden",
        "Community Garden Collective",
    ),
    (
        "Report broken streetlights near the bus stop",
        "Record pole numbers and locations from a safe public area, then submit a consolidated maintenance request. Electrical repairs are handled by the utility.",
        "Public safety",
        ["documentation"],
        "Beginner",
        1,
        "Cedar Avenue bus stop",
        "Neighborhood Safety Team",
    ),
    (
        "Run a winter coat donation drive",
        "Coordinate collection locations, organize donated coats by size, and arrange delivery to the community center.",
        "Community support",
        ["coordination", "organization"],
        "Intermediate",
        5,
        "Northside Community Center",
        "Community Support Network",
    ),
    (
        "Read with children at the community library",
        "Support a supervised reading session by listening to children read and helping them choose books. The library coordinates volunteer screening and orientation.",
        "Education",
        ["teaching", "communication"],
        "Intermediate",
        2,
        "Elm Street Library",
        "Library Learning Team",
    ),
    (
        "Survey sidewalk accessibility around the park",
        "Use a checklist to document missing curb ramps, blocked paths, and uneven surfaces. Prepare a summary for the accessibility coordinator.",
        "Accessibility",
        ["accessibility", "documentation"],
        "Intermediate",
        3,
        "Greenfield Park perimeter",
        "Access for Everyone",
    ),
    (
        "Help neighbors fill out food assistance forms",
        "Help residents navigate publicly available application instructions at a supervised information table. Refer eligibility and legal questions to the trained staff.",
        "Community support",
        ["communication", "organization"],
        "Intermediate",
        3,
        "Community Resource Hub",
        "Resource Navigation Team",
    ),
    (
        "Translate the food pantry welcome leaflet",
        "Translate the short welcome leaflet into Spanish and work with a second reviewer to check that opening hours and instructions are clear.",
        "Food security",
        ["translation", "communication"],
        "Intermediate",
        2,
        "Westside Food Pantry",
        "Food Pantry Volunteers",
    ),
    (
        "Organize a neighborhood recycling workshop",
        "Plan a hands-on session about the local recycling guide, prepare example sorting stations, and help residents identify accepted materials.",
        "Environment",
        ["teaching", "coordination"],
        "Intermediate",
        4,
        "Northside Community Center",
        "Green Neighborhood Team",
    ),
    (
        "Collect feedback about unsafe pedestrian crossings",
        "Gather resident observations and map locations needing review. Share the summary with the transport coordinator; the demo does not authorize traffic-control work.",
        "Transportation",
        ["communication", "documentation"],
        "Beginner",
        2,
        "School Street crossing",
        "Safe Routes Team",
    ),
    (
        "Prepare care packages for older residents",
        "Assemble care packages from the supplied checklist and label them for collection by the support team. No personal recipient data is used in this demo.",
        "Community support",
        ["organization", "teamwork"],
        "Beginner",
        2,
        "Northside Community Center",
        "Neighbor Support Team",
    ),
    (
        "Repair benches during the supervised park workday",
        "Assist the authorized park maintenance lead with sanding and repainting benches. Tools, supervision, and task assignments are provided by the organizer.",
        "Public spaces",
        ["maintenance", "teamwork"],
        "Advanced",
        6,
        "Greenfield Park",
        "Parks Volunteer Team",
    ),
    (
        "Organize a community blood-drive check-in desk",
        "Welcome visitors, help manage the appointment queue, and direct donors to professional staff. Volunteers do not perform medical procedures.",
        "Health",
        ["communication", "organization"],
        "Beginner",
        3,
        "Riverside Community Hall",
        "Community Health Volunteers",
    ),
    (
        "Map locations that need public rubbish bins",
        "Walk the designated neighborhood route, document litter hotspots, and compile suggested bin locations for municipal review.",
        "Environment",
        ["documentation", "coordination"],
        "Beginner",
        2,
        "Market Street district",
        "Clean Streets Team",
    ),
    (
        "Tutor adults in basic digital skills",
        "Help learners practice using email, finding public services, and completing a sample online form during a supervised drop-in session.",
        "Education",
        ["teaching", "communication"],
        "Intermediate",
        3,
        "Elm Street Library",
        "Library Learning Team",
    ),
]


def get_demo_repository(db):
    repo = db.scalar(
        select(Repository).where(
            Repository.source == "demo", Repository.path == DEMO_PATH
        )
    )
    if not repo:
        repo = Repository(source="demo", path=DEMO_PATH)
        # A savepoint tolerates concurrent first-time issue submissions.
        try:
            with db.begin_nested():
                db.add(repo)
                db.flush()
        except IntegrityError:
            repo = db.scalar(
                select(Repository).where(
                    Repository.source == "demo", Repository.path == DEMO_PATH
                )
            )
    return repo


def seed_demo(db):
    repo = get_demo_repository(db)
    added = 0
    for number, (
        title,
        description,
        topic,
        skills,
        difficulty,
        effort,
        location,
        organizer,
    ) in enumerate(ISSUES, 1):
        source_id = f"sample-{number:02d}"
        if db.scalar(
            select(Task.id).where(
                Task.repository_id == repo.id, Task.source_id == source_id
            )
        ):
            continue
        db.add(
            Task(
                repository_id=repo.id,
                source_id=source_id,
                title=title,
                description=description,
                url="",
                status="open",
                labels=[topic],
                metadata_fields={
                    "skills": skills,
                    "topics": [topic],
                    "difficulty": difficulty,
                    "effort": effort,
                    "location": location,
                    "organizer": organizer,
                    "demo_sample": True,
                    "provenance": "Fictional sample issue in the local demo repository.",
                },
            )
        )
        added += 1
    db.commit()
    return added


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        print(f"{DEMO_NAME}: added {seed_demo(db)} sample issues")
