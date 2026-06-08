const mongoose = require('mongoose');

//  User Schema
const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
  },
  email: {
    type: String,
    required: true,
    unique: true,
  },
  password: {
    type: String,
    required: true,
  },
  location: {
    type: String,
    required: true,
  },
    role: {
    type: String,
    enum: ['user', 'doctor', 'admin'],
    default: 'user',
    required: true,
  },
  createdAt: {
    type: Date,
    default: Date.now,
  },
}, { timestamps: true });


// Export User Model
module.exports = mongoose.model('User', userSchema);
