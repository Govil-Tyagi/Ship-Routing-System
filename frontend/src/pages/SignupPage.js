import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Navigation, Mail, Lock, User, Eye, EyeOff, UserCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SignupPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    // Validate password length
    if (formData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);

    try {
      // Create account
      await axios.post(`${API}/auth/signup`, {
        email: formData.email,
        username: formData.username,
        password: formData.password,
        full_name: formData.full_name || null
      });

      toast.success('Account created successfully!');

      // Auto-login after signup
      const loginResponse = await axios.post(`${API}/auth/login`, {
        email: formData.email,
        password: formData.password
      });

      if (loginResponse.data.access_token) {
        login(loginResponse.data.access_token, loginResponse.data.user);
        toast.success(`Welcome aboard, ${loginResponse.data.user.username}!`);
        navigate('/');
      }
    } catch (error) {
      console.error('Signup error:', error);
      const errorMessage = error.response?.data?.detail || 'Registration failed. Please try again.';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] flex items-center justify-center p-4" data-testid="signup-page">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2338BDF8' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }} />
      </div>

      <Card className="w-full max-w-md bg-slate-900/80 backdrop-blur-xl border-slate-700/50 relative z-10">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto p-3 bg-sky-500/20 rounded-xl w-fit">
            <Navigation className="h-8 w-8 text-sky-400" />
          </div>
          <div>
            <CardTitle className="text-2xl font-heading font-bold text-slate-100">Create Account</CardTitle>
            <CardDescription className="text-slate-400">
              Join the Marine Routing System
            </CardDescription>
          </div>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-300 text-sm font-medium">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="captain@vessel.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="pl-10 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-sky-500 focus:ring-sky-500/20"
                  data-testid="signup-email-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="username" className="text-slate-300 text-sm font-medium">Username</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <Input
                  id="username"
                  name="username"
                  type="text"
                  placeholder="captain_jack"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  minLength={3}
                  className="pl-10 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-sky-500 focus:ring-sky-500/20"
                  data-testid="signup-username-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="full_name" className="text-slate-300 text-sm font-medium">Full Name (Optional)</Label>
              <div className="relative">
                <UserCircle className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <Input
                  id="full_name"
                  name="full_name"
                  type="text"
                  placeholder="Jack Sparrow"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="pl-10 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-sky-500 focus:ring-sky-500/20"
                  data-testid="signup-fullname-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-300 text-sm font-medium">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  minLength={6}
                  className="pl-10 pr-10 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-sky-500 focus:ring-sky-500/20"
                  data-testid="signup-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-slate-300 text-sm font-medium">Confirm Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  className="pl-10 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-sky-500 focus:ring-sky-500/20"
                  data-testid="signup-confirm-password-input"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-sky-500 hover:bg-sky-400 text-slate-900 font-semibold"
              data-testid="signup-submit-btn"
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                  Creating Account...
                </div>
              ) : (
                'Create Account'
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-400 text-sm">
              Already have an account?{' '}
              <Link 
                to="/login" 
                className="text-sky-400 hover:text-sky-300 font-medium"
                data-testid="login-link"
              >
                Sign In
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SignupPage;
