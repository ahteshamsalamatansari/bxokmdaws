const User = require('../models/User');

exports.register = async (req, res, next) => {
  const { username, email, password } = req.body;
  if (!username || !email || !password) {
    return res.status(400).json({ success: false, error: 'Please provide all details' });
  }
  res.status(200).json({ success: true, data: 'Validation completed' });
};