# 🧠 Bleau.Info Statistics API
This API provides statistical data for bouldering repetitions in the Fontainebleau area. All data is extracted from bleau.info. It exposes multiple endpoints to query repetition counts, grades, monthly activity, and other metrics. It is designed to be consumed by a frontend interface (e.g., React) and optimized for read-only access in production.

## 🚀 Features
Access statistical bouldering data by area, grade, and time
Clean architecture with SQLAlchemy and Pydantic
Read-only database support (SQLite)

## 📦 Tech Stack
* Backend Framework: FastAPI
* ORM: SQLAlchemy
* Database: SQLite (local)


## API Endpoints

All endpoints are `GET` requests.

### 🧗‍♂️ Boulders
- `/boulders`: List all boulders (supports pagination and filtering, e.g., by style)
- `/boulders/{id}`: Get details of a specific boulder

### 🗺️ Areas
- `/areas`: List all areas  
- `/areas/{id}`: Get details of a specific area  
- `/areas/{id}/boulders`: List all boulders in a given area  
- `/areas/{id}/stats`: Get area stats (boulder count, grade distribution, most climbed boulder, average difficulty, total repetitions)

### 🌍 Regions
- `/regions`: List all regions  
- `/regions/{id}/areas`: List all areas in a region

### 👤 Users
- `/users`: List all users  
- `/users/{id}`: Get user details  
- `/users/{id}/boulders/set`: List of boulders set by the user  
- `/users/{id}/boulders/repeats`: List of boulders repeated by the user  
- `/users/{id}/stats`: User stats (total repeats, grade distribution, average grade, hardest climb, most climbed area, etc.)

### 🔍 Search
- `/{test}`: Search Boulders and Areas matching the `text`

### 📊 Statistics

#### Boulders
- `/stats/boulders/top-rated/{grade}`: Top 10 rated boulders for a specific grade  
- `/stats/boulders/most-ascents/{grade}`: Top 10 most repeated boulders  
- `/stats/boulders/hardest`: Boulders graded 8c and above  
- `/stats/boulders/styles/distribution`: Count of boulders per style  
- `/stats/boulders/ratings/distribution`: Count of boulders per rating

#### Areas
- `/stats/areas/most-ascents`: Top 10 areas with most repeats

#### Grades
- `/stats/grades/distribution`: Number of boulders per grade

#### Users
- `/stats/users/top-setters`: Top 10 users by number of boulders set  
- `/stats/users/top-repeaters`: Top 10 users by number of boulders repeated  
- `/stats/users/repeat-volume`: Histogram of users by repeat volume

#### Repeats
- `/stats/ascents/per-month`: Monthly ascents percentage distribution  
- `/stats/ascents/per-year`: Total number of ascents per year
- `/stats/ascents/per-grade`: Total number of ascents per grade
