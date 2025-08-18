from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

# TODO- features I may want to add
#Charts showing performance
#A way to upload assignments and give admins the opportunity to assign different types of  assignments
#Custom logic to determine performance
#Email system for notifications and alerts when assignments are created or due
#User profile for each user with pictures, bio and other basic information
#Announcements tab for each program apart from tasks, and assignments