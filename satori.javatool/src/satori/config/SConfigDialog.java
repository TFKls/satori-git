package satori.config;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;

import satori.main.SFrame;
import satori.session.SSession;

public class SConfigDialog {
	private JDialog dialog;
	private JPanel field_pane, button_pane;
	private JTextField host, thrift_port, blobs_port;
	private JCheckBox use_ssl;
	private JButton confirm, cancel;
	private boolean confirmed = false;
	
	private SConfigDialog() {
		initialize();
	}
	
	private void initialize() {
		dialog = new JDialog(SFrame.get().getFrame(), "Server configuration", true);
		dialog.getContentPane().setLayout(new BorderLayout());
		field_pane = new JPanel();
		field_pane.setLayout(new GridBagLayout());
		GridBagConstraints c = new GridBagConstraints();
		c.gridx = 0; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 0.0; c.weighty = 0.0;
		field_pane.add(new JLabel("Server: "), c);
		field_pane.add(new JLabel("Thrift port: "), c);
		field_pane.add(new JLabel("Blobs port: "), c);
		c.gridx = 1; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 1.0; c.weighty = 0.0;
		ActionListener confirm_listener = new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				confirmed = true;
				dialog.setVisible(false);
			}
		};
		host = new JTextField(SConfig.getHost());
		host.setPreferredSize(new Dimension(200, host.getPreferredSize().height));
		host.addActionListener(confirm_listener);
		field_pane.add(host, c);
		thrift_port = new JTextField(String.valueOf(SConfig.getThriftPort()));
		thrift_port.setPreferredSize(new Dimension(75, thrift_port.getPreferredSize().height));
		thrift_port.addActionListener(confirm_listener);
		field_pane.add(thrift_port, c);
		blobs_port = new JTextField(String.valueOf(SConfig.getBlobsPort()));
		blobs_port.setPreferredSize(new Dimension(75, blobs_port.getPreferredSize().height));
		blobs_port.addActionListener(confirm_listener);
		field_pane.add(blobs_port, c);
		use_ssl = new JCheckBox("Use SSL", SConfig.getUseSSL());
		use_ssl.setPreferredSize(new Dimension(75, use_ssl.getPreferredSize().height));
		field_pane.add(use_ssl, c);
		dialog.getContentPane().add(field_pane, BorderLayout.CENTER);
		button_pane = new JPanel();
		button_pane.setLayout(new FlowLayout(FlowLayout.CENTER));
		confirm = new JButton("Save");
		confirm.addActionListener(confirm_listener);
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
		dialog.setLocationRelativeTo(SFrame.get().getFrame());
	}
	
	private void process() {
		dialog.setVisible(true);
		if (!confirmed) return;
		SConfig.setHost(host.getText());
		SConfig.setThriftPort(Integer.valueOf(thrift_port.getText()));
		SConfig.setBlobsPort(Integer.valueOf(blobs_port.getText()));
		SConfig.setUseSSL(use_ssl.isSelected());
		SSession.logout();
		SConfig.save();
	}
	
	public static void show() {
		SConfigDialog self = new SConfigDialog();
		self.process();
	}
}
