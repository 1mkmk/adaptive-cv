# This file makes the directory a Python package
# Instead of creating a central router that includes all other routers,
# we'll simply make the routers available for import

# This ensures the routers can be imported from the main.py file
# and avoids duplicate registration
"""
Routers for the API
These routers should be imported and registered in the main.py file
"""

from .jobs import router as jobs_router
from .generate import router as generate_router
from .profile import router as profile_router
from .auth import router as auth_router