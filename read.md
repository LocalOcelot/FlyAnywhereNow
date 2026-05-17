```mermaid
flowchart TD
app[app]
Search[Flightsearch]
Interactions[Flight Database Interactions]
Scraper[Scraper]
DB[(FlightDB)]

app --> Search
Search --> Interactions
Interactions --> Scraper
Interactions --> DB
```