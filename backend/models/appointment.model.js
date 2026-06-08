const mongoose = require('mongoose');

const appointmentSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    doctor: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Doctor',
      required: true,
    },
    date: {
      type: String,
      required: true,
    },
    time: String,

    description: {
      type: String,
      required: true,
    },

    roomId: {
      type: String,
      default: () => new mongoose.Types.ObjectId().toString(),
      unique: true,
    },

    prescription: {
      medicines: [String],
      notes: String,
      precautions: String,
    },
    suggestedTests: [String],

    testReports: [
      {
        url: String,
        uploadedAt: Date,
      }
    ],

    review: String,

    callStartedAt: Date,
    callEndedAt: Date,

    completedAt: Date,

    paymentId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Payment"
    },
    paymentStatus: {
      type: String,
      enum: ['pending', 'paid', 'failed'],
      default: 'pending'
    },

    isFollowUp: {
      type: Boolean,
      default: false,
    },
    status: {
      type: String,
      enum: [
        'pending',
        'ongoing',
        'awaiting_prescription',
        'completed',
        'cancelled'
      ],
      default: 'pending',
    },
  },
  { timestamps: true }
);

module.exports = mongoose.model('Appointment', appointmentSchema);
