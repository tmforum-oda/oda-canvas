package org.tmform.oda.canvas.portal.configuration;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.ProviderManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.factory.PasswordEncoderFactories;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.LoginUrlAuthenticationEntryPoint;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.security.web.util.matcher.AntPathRequestMatcher;
import org.tmform.oda.canvas.portal.login.OdaUser;

@Configuration
@EnableWebSecurity
@EnableConfigurationProperties(OdaUser.class)
public class SecurityConfig {

	@Bean
	public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
		http
				.authorizeHttpRequests((authorize) -> authorize
						.requestMatchers(new AntPathRequestMatcher("/login**")).permitAll()
						.anyRequest().authenticated()

				).exceptionHandling((exceptionHandling) ->
						exceptionHandling
								.authenticationEntryPoint(authenticationEntryPoint()))
				.csrf(AbstractHttpConfigurer::disable);

		return http.build();
	}

	@Bean
	public LoginUrlAuthenticationEntryPoint authenticationEntryPoint(){
		return new LoginUrlAuthenticationEntryPoint("/login.html");
	}

	@Bean
	public SecurityContextRepository securityContextRepository(){
		return new HttpSessionSecurityContextRepository();
	}


	@Bean
	public UserDetailsService userDetailsService(OdaUser odaUser) {
		UserDetails userDetails = User.builder()
			.username(odaUser.getUserName())
			.password(odaUser.getPassword())
			.build();

		return new InMemoryUserDetailsManager(userDetails);
	}

	@Bean
	public AuthenticationManager authenticationManager(
			UserDetailsService userDetailsService,
			PasswordEncoder passwordEncoder) {
		DaoAuthenticationProvider authenticationProvider = new DaoAuthenticationProvider();
		authenticationProvider.setUserDetailsService(userDetailsService);
		authenticationProvider.setPasswordEncoder(passwordEncoder);

		return new ProviderManager(authenticationProvider);
	}

	@Bean
	public PasswordEncoder passwordEncoder() {
		return PasswordEncoderFactories.createDelegatingPasswordEncoder();
	}

}