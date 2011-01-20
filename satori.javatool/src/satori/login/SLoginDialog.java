package satori.login;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;

import satori.common.SException;
import satori.main.SFrame;

public class SLoginDialog {
	private JDialog dialog;
	private JPanel field_pane, button_pane;
	private JTextField username;
	private JPasswordField password;
	private JButton confirm, cancel;
	private boolean confirmed = false;
	
	private SLoginDialog() {
		initialize();
	}
	
	private void initialize() {
		dialog = new JDialog(SFrame.get().getFrame(), "Login", true);
		dialog.getContentPane().setLayout(new BorderLayout());
		field_pane = new JPanel();
		field_pane.setLayout(new GridBagLayout());
		GridBagConstraints c = new GridBagConstraints();
		c.gridx = 0; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 0.0; c.weighty = 0.0;
		field_pane.add(new JLabel("User: "), c);
		field_pane.add(new JLabel("Password: "), c);
		c.gridx = 1; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 1.0; c.weighty = 0.0;
		username = new JTextField(SLogin.getLogin());
		username.setPreferredSize(new Dimension(200, username.getPreferredSize().height));
		field_pane.add(username, c);
		password = new JPasswordField(SLogin.getPassword());
		password.setPreferredSize(new Dimension(200, password.getPreferredSize().height));
		field_pane.add(password, c);
		dialog.getContentPane().add(field_pane, BorderLayout.CENTER);
		button_pane = new JPanel();
		button_pane.setLayout(new FlowLayout(FlowLayout.CENTER));
		confirm = new JButton("Login");
		confirm.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				confirmed = true;
				dialog.setVisible(false);
			}
		});
		button_pane.add(confirm);
		cancel = new JButton("Cancel");
		cancel.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				dialog.setVisible(false);
			}
		});
		button_pane.add(cancel);
		dialog.getContentPane().add(button_pane, BorderLayout.SOUTH);
		dialog.pack();
	}
	
	private void process() throws SException {
		dialog.setVisible(true);
		if (!confirmed) return;
		SLogin.login(username.getText(), new String(password.getPassword()));
	}
	
	public static void show() throws SException {
		SLoginDialog self = new SLoginDialog();
		self.process();
	}
}