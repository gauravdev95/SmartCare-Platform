const express = require('express');
const router = express.Router();
const adminController = require('../controllers/admin.controller');
const { auth } = require('../middleware/auth'); 


// Admin routes
router.post('/login', adminController.login);
router.post('/register', adminController.register);
router.get('/profile', auth, adminController.profile);


// Verify doctor route - only accessible by admin
router.get('/unverified-doctors',auth, adminController.getUnverifiedDoctors);
router.put('/verify-doctor/:id', auth, adminController.verifyDoctor);
router.get('/stats', auth, adminController.getAdminStats);


// Export the router
module.exports = router;
