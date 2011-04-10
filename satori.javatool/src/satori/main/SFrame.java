package satori.main;

import java.awt.BorderLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;

import satori.common.SAssert;
import satori.common.SException;
import satori.common.SView;
import satori.common.ui.STabbedPane;
import satori.config.SConfig;
import satori.config.SConfigDialog;
import satori.problem.ui.SProblemListPane;
import satori.session.SLoginDialog;
import satori.session.SSession;
import satori.task.STaskException;

public class SFrame {
	private STabbedPane tabs = new STabbedPane();
	
	private JFrame frame;
	private JMenu session_menu, open_menu;
	private JMenuItem login_button, anonymous_button, logout_button, config_button;
	private JMenuItem problems_button;
	private JLabel session_label;
	
	private SFrame() {
		initialize();
		SSession.addView(new SView() {
			@Override public void update() { updateSession(); }
		});
	}
	
	public JFrame getFrame() { return frame; }
	
	private void updateSession() {
		SSession session = SSession.get();
		if (session == null) { session_label.setText("Session: disconnected"); return; }
		String username = session.getUsername() != null ? session.getUsername() : "<anonymous>";
		session_label.setText("Session: " + username + "@" + session.getHost());
	}
	
	private void loginRequest() {
		try { SLoginDialog.show(); }
		catch(STaskException ex) { return; }
		updateSession();
	}
	private void anonymousLoginRequest() {
		try { SSession.anonymousLogin(); }
		catch(STaskException ex) { return; }
		updateSession();
	}
	private void logoutRequest() {
		try { SSession.logout(); }
		catch(STaskException ex) { return; }
		updateSession();
	}
	private void configRequest() {
		SConfigDialog.show();
	}
	private void problemsRequest() {
		SProblemListPane pane;
		try { pane = SProblemListPane.get(tabs); }
		catch(SException ex) { showErrorDialog(ex); return; }
		tabs.openPane("Problems", pane);
	}
	private void closeRequest() {
		if (tabs.hasUnsavedData() && !showWarningDialog("The window contains unsaved data.")) return;
		tabs.closeAll();
		System.exit(0);
	}
	
	private void initialize() {
		frame = new JFrame("Satori Tool");
		frame.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
		frame.getContentPane().setLayout(new BorderLayout());
		frame.getContentPane().add(tabs.getPane(), BorderLayout.CENTER);
		session_label = new JLabel();
		frame.getContentPane().add(session_label, BorderLayout.NORTH);
		
		JMenuBar menu_bar = new JMenuBar();
		session_menu = new JMenu("Session");
		login_button = new JMenuItem("Login...");
		login_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				loginRequest();
			}
		});
		session_menu.add(login_button);
		anonymous_button = new JMenuItem("Anonymous login");
		anonymous_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				anonymousLoginRequest();
			}
		});
		session_menu.add(anonymous_button);
		logout_button = new JMenuItem("Logout");
		logout_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				logoutRequest();
			}
		});
		session_menu.add(logout_button);
		config_button = new JMenuItem("Server configuration...");
		config_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				configRequest();
			}
		});
		session_menu.add(config_button);
		menu_bar.add(session_menu);
		open_menu = new JMenu("Open");
		problems_button = new JMenuItem("Problems");
		problems_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				problemsRequest();
			}
		});
		open_menu.add(problems_button);
		menu_bar.add(open_menu);
		frame.setJMenuBar(menu_bar);
		frame.addWindowListener(new WindowAdapter() {
			@Override public void windowClosing(WindowEvent e) { closeRequest(); }
		});
		updateSession();
		
		frame.setSize(960, 720);
	}
	
	public void start() {
		SConfig.load();
		if (!SConfig.hasConfig()) SConfigDialog.show();
		frame.setVisible(true);
	}
	
	private static SFrame instance = null;
	
	public static SFrame get() { return instance; }
	
	public static void setInstance() {
		SAssert.assertNull(instance, "Multiple frame instance");
		instance = new SFrame();
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
