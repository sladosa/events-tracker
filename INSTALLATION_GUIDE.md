# 🔐 Authentication Setup - Installation Guide

## 📦 Package Contents

This package contains everything you need to add authentication to your Events Tracker app:

1. **auth.py** - Authentication module (goes in `/src/`)
2. **streamlit_app_with_auth.py** - Modified main app file (replaces `streamlit_app.py`)
3. **complete_auth_setup.sql** - SQL to setup database with RLS

## 🚀 Installation Steps

### STEP 1: Backup Your Current Files ⚠️

**IMPORTANT**: Backup before making changes!

```bash
cd events-tracker
cp streamlit_app.py streamlit_app_BACKUP.py
```

### STEP 2: Copy New Files

1. **Copy auth.py to src folder**:
   ```
   events-tracker/
   └── src/
       ├── auth.py  ← PUT IT HERE
       ├── excel_parser.py
       ├── sql_generator.py
       └── ...
   ```

2. **Replace streamlit_app.py**:
   - Rename `streamlit_app_with_auth.py` → `streamlit_app.py`
   - Or copy its content and replace your current `streamlit_app.py`

### STEP 3: Run SQL in Supabase

1. Open **Supabase Dashboard** → **SQL Editor**
2. Create **New query**
3. Open `complete_auth_setup.sql` in text editor
4. **Copy ALL** content
5. **Paste** into Supabase SQL Editor
6. Click **RUN** (bottom right)
7. Wait ~5 seconds

**Expected output**: Should see verification results showing user_id columns added and RLS enabled

### STEP 4: Enable Email in Supabase Auth

1. Go to **Supabase Dashboard** → **Authentication** → **Providers**
2. Find **Email** provider
3. Make sure it's **ENABLED** (should be by default)
4. **Confirm email** setting:
   - Recommended: **Enabled** (users must confirm email)
   - Or: **Disabled** (for testing only)

### STEP 5: Test the Application

1. **Restart Streamlit**:
   ```bash
   streamlit run streamlit_app.py
   ```

2. **You should see Login/Signup screen!** 🎉

3. **Create Account**:
   - Click "Sign Up" tab
   - Enter email (your real email)
   - Enter password (min 6 characters)
   - Confirm password
   - Click "Sign Up"

4. **Check Email**:
   - Look for confirmation email from Supabase
   - Click confirmation link
   - (If email doesn't arrive in 5 min, check spam)

5. **Login**:
   - Return to app
   - Enter your email/password
   - Click "Login"
   - **Welcome!** 🎊

6. **Upload Template**:
   - Now you can upload `garmin_fitness_template_fixed.xlsx`
   - Data will be saved with YOUR user_id
   - Secured with RLS - only you can see your data!

## 🔍 Troubleshooting

### "Module 'auth' not found"
- Make sure `auth.py` is in `src/` folder
- Check file name is exactly `auth.py` (lowercase)

### "Invalid login credentials"
- Make sure you confirmed your email
- Check password is correct
- Try "Sign Up" if you haven't created account yet

### "Column user_id does not exist"
- Make sure you ran `complete_auth_setup.sql`
- Check SQL completed without errors

### Can't see old data (NULL user_id)
- Old data with `user_id = NULL` won't be visible
- This is expected behavior with RLS
- Solution: Upload template again (will create data with your user_id)

## ✅ Verification Checklist

After installation, verify:

- [ ] Login/Signup screen appears on app start
- [ ] Can create new account
- [ ] Receive confirmation email
- [ ] Can login successfully
- [ ] See user email in sidebar
- [ ] Can logout
- [ ] Export Structure works (may be empty if no data)
- [ ] Upload Template works
- [ ] Data appears in Supabase with your user_id

## 🎯 What Changed

### Database:
- ✅ Added `user_id` columns to all tables
- ✅ Added foreign keys to `auth.users`
- ✅ Enabled Row Level Security (RLS)
- ✅ Created RLS policies (users see only their data)

### Application:
- ✅ Added authentication module (`auth.py`)
- ✅ Login/Signup interface
- ✅ Session management
- ✅ User info display in sidebar
- ✅ Logout functionality
- ✅ All operations now filter by user_id

## 📚 Next Steps

After authentication is working:

1. **Customize Your Template**:
   - Export your structure
   - Edit in Excel
   - Re-upload to apply changes

2. **Add Events** (coming soon):
   - Event entry interface
   - Data visualization
   - Analytics

3. **Optional Enhancements**:
   - Google/GitHub OAuth login
   - Password reset functionality
   - Profile management
   - Team/organization support

## 🆘 Need Help?

If you encounter issues:

1. Check this README carefully
2. Verify all files are in correct locations
3. Check Supabase SQL output for errors
4. Restart Streamlit app
5. Check browser console for errors (F12)

---

**Good luck! 🚀**

Made with ❤️ by Claude
