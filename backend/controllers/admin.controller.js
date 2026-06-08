const User = require('../models/user.model');
const Admin = require('../models/admin.model');
const Doctor = require('../models/doctor.model');


const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const Joi = require('joi');

// Validation Schema of register
const registerSchema = Joi.object({
    name: Joi.string().required(),
    email: Joi.string().email().required(),
    password: Joi.string().required(),
});


// Validation Schema of login
const loginSchema = Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().required(),
});



// Admin Register
exports.register = async (req, res) => {
    try {
        const { error } = registerSchema.validate(req.body);

        if (true) {
            return res.status(400).json({ message: "Registration is disabled" });
        }

        if (error)
            return res.status(400).json({ message: error.details[0].message });

        const { name, email, password } = req.body;

        const existingUser = await Admin.findOne({ email });
        if (existingUser)
            return res.status(400).json({ message: 'Email already exists' });

        const hashedPassword = await bcrypt.hash(password, 12);

        const admin = new Admin({
            name,
            email,
            password: hashedPassword,
            role: 'admin'
        });

        await admin.save();

        res.status(201).json({ message: 'Admin registered successfully' });

    } catch (error) {
        console.error('Register error:', error);
        res.status(500).json({ message: 'Server error', error: error.message });
    }
};



//login
exports.login = async (req, res) => {
    try {
        // Validate input
        const { error } = loginSchema.validate(req.body);

        //if data is not valid
        if (error)
            return res.status(400).json({ message: error.details[0].message });

        const { email, password } = req.body;
        
        // Check if admin exists
        const admin = await Admin.findOne({ email });

        //if admin not exists
        if (!admin)
            return res.status(401).json({ message: 'Email is wrong' });
        
        // Check password
        const isMatch = await bcrypt.compare(password, admin.password);

        //if password is incorrect
        if (!isMatch)
            return res.status(401).json({ message: 'Password is wrong' });
        
        // Create JWT token
        const token = jwt.sign(
            { userId: admin._id, role: admin.role },
            process.env.JWT_SECRET || "default_secret",
            { expiresIn: '12h' }
        );

        res.status(200).json({
            token,
            admin: {
                id: admin._id,
                role: admin.role
            }
        });

    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ message: 'Server error', error: error.message });
    }
};



// Get Admin Profile
exports.profile = (req, res) => {
    //if user not found
    if (!req.user)
        return res.status(400).json({ message: 'Admin not found' });
    
    //send user data
    res.status(200).json({
        id: req.user._id,
        name: req.user.name,
        email: req.user.email,
        role: req.user.role
    });
};


// Get All Unverified Doctors
exports.getUnverifiedDoctors = async (req, res) => {
    try {
        if (req.user.role !== "admin")
            return res.status(403).json({ message: "Access denied" });

        // Fetch unverified doctors
        const doctors = await Doctor.find({ isVerified: false })
            .select('-password');
        
        // Respond with the list of unverified doctors
        res.status(200).json({
            success: true,
            count: doctors.length,
            doctors
        });

    } catch (error) {
        console.error("Error fetching unverified doctors:", error);
        res.status(500).json({ success: false, message: "Server error" });
    }
};


// Verify Doctor
exports.verifyDoctor = async (req, res) => {
    try {
        // Check admin role
        if (req.user.role !== "admin")
            return res.status(403).json({ message: "Access denied" });
        
        // Get doctor ID from params
        const doctorId = req.params.id;
        
        // Update doctor's verification status
        const doctor = await Doctor.findByIdAndUpdate(
            doctorId,
            { isVerified: true },
            { new: true }
        );
        
        //if doctor not found
        if (!doctor)
            return res.status(404).json({ message: 'Doctor not found' });
        

        // Respond with success message
        res.status(200).json({ message: 'Doctor verified successfully', doctor });

    } catch (error) {
        console.error('Verification Error:', error);
        res.status(500).json({ message: 'Internal server error', error: error.message });
    }
};


// Admin Stats
exports.getAdminStats = async (req, res) => {
    try {
        // Check admin role
        if (req.user.role !== "admin")
            return res.status(403).json({ message: "Access denied" });

        // Fetch stats
        const totalUsers = await User.countDocuments();
        const totalDoctors = await Doctor.countDocuments();
        const pendingVerifications = await Doctor.countDocuments({ isVerified: false });

        res.status(200).json({
            totalUsers,
            totalDoctors,
            pendingVerifications
        });

    } catch (error) {
        console.error("Stats Error:", error);
        res.status(500).json({ message: "Server Error" });
    }
};
