package satori.config;

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
import javax.swing.JTextField;

import satori.main.SFrame;

public class SConfigDialog {
	private JDialog dialog;
	private JPanel field_pane, button_pane;
	private JTextField host, thrift_port, blobs_port;
	private JButton confirm, cancel;
	private boolean confirmed = false;
	
	private SConfigDialog() {
		initialize();
	}
	
	private void initialize() {
		dialog = new JDialog(SFrame.get().getFrame(), "Configuration", true);
		dialog.getContentPane().setLayout(new BorderLayout());
		field_pane = new JPanel();
		field_pane.setLayout(new GridBagLayout());
		GridBagConstraints c = new GridBagConstraints();
		c.gridx = 0; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 0.0; c.weighty = 0.0;
		field_pane.add(new JLabel("Server: "), c);
		field_pane.add(new JLabel("Thrift port: "), c);
		field_pane.add(new JLabel("Blobs port: "), c);
		c.gridx = 1; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 1.0; c.weighty = 0.0;
		host = new JTextField(SConfig.getHost());
		host.setPreferredSize(new Dimension(200, host.getPreferredSize().height));
		field_pane.add(host, c);
		thrift_port = new JTextField(String.valueOf(SConfig.getThriftPort()));
		thrift_port.setPreferredSize(new Dimension(75, thrift_port.getPreferredSize().height));
		field_pane.add(thrift_port, c);
		blobs_port = new JTextField(String.valueOf(SConfig.getBlobsPort()));
		blobs_port.setPreferredSize(new Dimension(75, blobs_port.getPreferredSize().height));
		field_pane.add(blobs_port, c);
		dialog.getContentPane().add(field_pane, BorderLayout.CENTER);
		button_pane = new JPanel();
		button_pane.setLayout(new FlowLayout(FlowLayout.CENTER));
		confirm = new JButton("Save");
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
	
	private void process() {
		dialog.setVisible(true);
		if (!confirmed) return;
		SConfig.save(host.getText(), Integer.valueOf(thrift_port.getText()), Integer.valueOf(blobs_port.getText()));
	}
	
	public static void show() {
		SConfigDialog self = new SConfigDialog();
		self.process();
	}
}
