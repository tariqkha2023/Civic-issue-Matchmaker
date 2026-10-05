The image is a **layered system architecture diagram** titled **“Civic Issue Matchmaker – Layered System Architecture.”** It is laid out as a large rectangular diagram with the system’s internal layers stacked vertically from top to bottom, and external systems shown off to the right. Arrows indicate communication between components. The color scheme distinguishes architectural layers and external services.

Starting at the very top center is the title, in bold black text: **“Civic Issue Matchmaker – Layered System Architecture.”**

The main system occupies most of the left and center of the image. Along the far left is a vertical sequence of four labeled layer boxes, numbered 1 through 4. Each aligns horizontally with the corresponding part of the architecture to its right.

**Layer 1 is the Presentation Layer.** Its label box is at the upper left, outlined in blue, and reads **“1. Presentation Layer (User Interfaces)”**. Beneath the label is a small blue icon depicting a desktop monitor and a smartphone, representing responsive user interfaces.

Directly to its right is a large blue-outlined rounded rectangle titled **“Web Client (Responsive Web Application)”**. Inside this web-client area are three horizontally arranged interface panels.

The first, on the left, is **“Volunteer Interface.”** It has a blue person icon. Its listed responsibilities are: **Register / Log In, profile, recommendations, tasks, feedback, history, etc.**

The middle panel is **“Maintainer Interface.”** It also has a blue person icon. Its description says: **Log In, review and correct derived metadata for authorized repositories.**

The right panel is **“Administrator Interface.”** It uses a blue shield icon. Its description says: **User/role management, sources, schedules, system settings, status, logs, etc.**

The three interface panels sit within the larger Web Client container and indicate three distinct user roles accessing the same responsive web application.

Below the Presentation Layer is **Layer 2, Application Services.** Its label box is on the left, also outlined in blue, and reads **“2. Application Services (Web Application)”**. A small blue gear icon appears beneath the label.

To the right is a long horizontal blue-outlined rectangle labeled **“Application Services.”** Inside it, centered, is a description of its role: **Business logic, request handling, validation, authorization (RBAC), and coordination of all system functions.**

A vertical arrow runs downward from the Web Client into this Application Services box, showing that the user interfaces send requests into the application-services layer.

Below this is **Layer 3, Domain & Business Services.** On the far left is a tall green-outlined box labeled **“3. Domain & Business Services (Core System Functions)”**. Near the bottom of this label box is an icon of three connected cubes, symbolizing modular business components.

The corresponding main area to the right is a large pale-green rectangle containing the core functional modules of the system. These are arranged mostly as two rows of four smaller rounded green boxes, followed by one wider box centered underneath them.

In the **top row**, from left to right:

**Account & Profile Management**  
Description: **Manage user accounts, profiles, skills, interests, preferences, availability.**

**Repository Connector & Task Aggregation**  
Description: **Connect to repositories, retrieve tasks, normalize metadata, detect changes.**

**Task Aggregation & Metadata Management**  
Description: **Canonical task store, tags, difficulty, skills, source mapping.**

**Recommendation & Matching Engine**  
Description: **Filter eligible tasks, score and rank, and generate explanations.**

In the **second row**, again from left to right:

**Participation & History**  
Description: **Manage saves, claims, releases, completions, and participation history.**

**Feedback Management**  
Description: **Collect relevance feedback and maintain feedback history.**

**Maintainer Metadata Correction**  
Description: **Review and correct derived metadata with audit trail (preserve source values).**

**Notification Management**  
Description: **Create in-app and email notifications and manage delivery records.**

Centered below those eight modules is a wider green box called **“Administration & System Management.”** Its description reads: **User/role management, repository sources, scan schedules, system settings, operational status, logs, and audit information.**

There is a downward arrow from Application Services into this Domain & Business Services area, indicating that the application layer invokes these core business functions.

Below the domain layer is **Layer 4, Persistence Layer.** Its label box appears on the left with an orange outline and reads **“4. Persistence Layer (Data Storage)”**. Beneath that text is a small orange database-cylinder icon.

To the right is a large orange-outlined persistence area. Inside it is a large database-cylinder shape labeled **“Relational Database.”** Beneath that title is a compact list of stored information: **Users, profiles, roles, tasks, metadata, skills, claims, feedback, notifications, source information, schedules, settings, audit logs, etc.**

A vertical two-way arrow connects the Domain & Business Services layer to this Relational Database. The arrow indicates that business services both read from and write to persistent storage.

Now moving to the **right side of the diagram**, there are two external-system areas.

The upper external area is a blue dashed rectangle titled **“External Repository Systems (Authorized Sources)”**. Inside it are three vertically arranged source types.

At the top is the GitHub logo with the text **“GitHub (Authorized Repositories)”**.

Below it is the GitLab logo with the text **“GitLab (Authorized Repositories)”**.

At the bottom is a simple database-cylinder icon with the text **“Future Authorized Repository Sources.”**

A dashed arrow runs from the main system toward this external repository box. Next to the arrow is the label **“Scheduled Scans (API Access)”**. This indicates that the Civic Issue Matchmaker periodically connects to authorized repository systems through APIs and scans them for issue/task information. The dashed arrow style is used because this interaction is asynchronous or scheduled rather than a direct synchronous request.

Lower down on the right is another external-system box outlined in orange dashed lines, titled **“Email Provider.”** Inside it is an orange envelope icon and the text **“Email Delivery Service.”**

A solid arrow connects the **Notification Management** module in the domain layer to the Email Provider. This shows that the system sends email notifications through an outside email-delivery service. Because the arrow is solid, it represents a synchronous interaction according to the diagram’s legend.

At the very bottom of the image is a horizontal **legend** enclosed in a light gray rectangle. It explains the visual notation.

The legend shows:

- A **blue-outlined rounded box** labeled **“Presentation / Application Layer”**.
- A **green-outlined rounded box** labeled **“Domain / Business Services”**.
- An **orange database-cylinder symbol** labeled **“Data Store”**.
- A **blue dashed rectangle** labeled **“External System”**.
- A **solid black arrow** labeled **“Synchronous Interaction”**.
- A **dashed black arrow** labeled **“Asynchronous / Scheduled Interaction”**.

Procedurally, the diagram can be read as a flow from top to bottom:

1. A user enters the system through one of three interfaces: Volunteer, Maintainer, or Administrator.
2. The Web Client sends the user’s request to Application Services.
3. Application Services handles request-level concerns such as validation, role-based authorization, business-logic coordination, and request routing.
4. Application Services invokes one or more Domain & Business Services modules.
5. Those domain modules perform specific system functions such as account management, repository ingestion, task aggregation, recommendation generation, participation tracking, feedback handling, maintainer correction, notifications, or administration.
6. The domain layer reads from and writes to the Relational Database to persist system state.
7. On a scheduled basis, the system contacts authorized GitHub, GitLab, and potentially future repository providers through their APIs to retrieve repository and task information.
8. When a notification requires email delivery, Notification Management sends the message to the external Email Delivery Service.

The overall architecture therefore depicts a **four-layer system**: **Presentation → Application Services → Domain/Business Services → Persistence**, with **external repository integrations** supplying task data and an **external email provider** delivering notifications.