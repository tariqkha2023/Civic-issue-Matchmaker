# CivicMatch (React + Vite)

Frontend for a civic issue matchmaker: search by skill/issue + location, filter by category, work type and urgency.

## Run
    npm install
    npm run dev      # http://localhost:5173
    npm run build    # production build in /dist

## Structure
    src/
      App.jsx              state + layout
      data.js              sample issues (replace with API)
      utils.js             search, match score, filter, sort
      components/          Header, Hero (search bar), Filters, IssueCard
