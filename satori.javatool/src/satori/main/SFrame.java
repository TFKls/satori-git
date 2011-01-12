package satori.main;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JFrame;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;

import satori.common.SException;
import satori.common.ui.STabbedPane;
import satori.config.SConfig;
import satori.config.SConfigDialog;
import satori.login.SLogin;
import satori.login.SLoginDialog;
import satori.problem.ui.SProblemListPane;

public class SFrame {
	private STabbedPane tabs = new STabbedPane();
	
	private JFrame frame;
	private JMenu session_menu, open_menu;
	private JMenuItem login_button, logout_button;
	private JMenuItem problems_button, config_button;
	
	private SFrame() { initialize(); }
	
	public JFrame getFrame() { return frame; }
	
	private void updateLogin() {
		if (SLogin.getLogin() != null) {
			session_menu.setText("Session (" + SLogin.getLogin() + ")");
		} else {
			session_menu.setText("Session");
		}
	}
	
	private void loginRequest() {
		try { SLoginDialog.show(); }
		catch(SException ex) { showErrorDialog(ex); return; }
		updateLogin();
	}
	private void logoutRequest() {
		try { SLogin.logout(); }
		catch(SException ex) { showErrorDialog(ex); return; }
		updateLogin();
	}
	
	private void problemsRequest() {
		SProblemListPane pane;
		try { pane = SProblemListPane.get(tabs); }
		catch(SException ex) { showErrorDialog(ex); return; }
		tabs.openPane("Problems", pane);
	}
	private void configRequest() {
		SConfigDialog.show();
	}
	
	private void initialize() {
		frame = new JFrame("Satori Tool");
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.getContentPane().add(tabs.getPane());
		
		JMenuBar menu_bar = new JMenuBar();
		//menu_bar.setLayout(new BorderLayout());
		//menu_bar.add(Box.createHorizontalGlue());
		session_menu = new JMenu();
		login_button = new JMenuItem("Login...");
		login_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				loginRequest();
			}
		});
		session_menu.add(login_button);
		logout_button = new JMenuItem("Logout");
		logout_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				logoutRequest();
			}
		});
		session_menu.add(logout_button);
		menu_bar.add(session_menu);
		open_menu = new JMenu("Open");
		problems_button = new JMenuItem("Problems");
		problems_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				problemsRequest();
			}
		});
		open_menu.add(problems_button);
		config_button = new JMenuItem("Configuration");
		config_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				configRequest();
			}
		});
		open_menu.add(config_button);
		menu_bar.add(open_menu);
		frame.setJMenuBar(menu_bar);
		updateLogin();
		
		frame.setSize(960, 720);
	}
	
	public void start() {
		//frame.pack();
		SConfig.load();
		if (!SConfig.hasConfig()) SConfigDialog.show();
		frame.setVisible(true);
	}
	
	private static SFrame instance = null;
	
	public static SFrame get() {
		if (instance == null) instance = new SFrame();
		return instance;
	}
	
	public static void showErrorDialog(String message) {
		JOptionPane.showMessageDialog(get().frame, message, "Error", JOptionPane.ERROR_MESSAGE);
	}
	public static void showErrorDialog(SException ex) {
		showErrorDialog(ex.getMessage());
	}
	public static boolean showWarningDialog(String message) {
		Object[] options = { "Continue", "Cancel" };
		return JOptionPane.showOptionDialog(get().frame, message, "Warning", JOptionPane.WARNING_MESSAGE, JOptionPane.OK_CANCEL_OPTION, null, options, options[0]) == JOptionPane.OK_OPTION;
	}
}
