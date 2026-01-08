package org.ossrag.meta.service;

import org.ossrag.meta.domain.User;
import org.ossrag.meta.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class UserService {
    
    private final UserRepository repository;
    private final PasswordEncoder passwordEncoder;
    
    public UserService(UserRepository repository, PasswordEncoder passwordEncoder) {
        this.repository = repository;
        this.passwordEncoder = passwordEncoder;
    }
    
    public boolean authenticateUser(String username, String password) {
        Optional<User> userOpt = repository.findByUsername(username);
        if (userOpt.isEmpty()) {
            return false;
        }
        
        User user = userOpt.get();
        // BCrypt로 비밀번호 검증
        return passwordEncoder.matches(password, user.getPassword());
    }
    
    public User findByUsername(String username) {
        return repository.findByUsername(username).orElse(null);
    }
    
    public User findById(Long id) {
        return repository.findById(id).orElse(null);
    }
    
    public User save(User user) {
        return repository.save(user);
    }
    
    public boolean existsByUsername(String username) {
        return repository.existsByUsername(username);
    }
    
    public boolean existsByEmail(String email) {
        return repository.existsByEmail(email);
    }
}
