package satori.problem.ui;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.Comparator;

import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.ListSelectionModel;

import satori.common.SListener0;
import satori.common.SListener1;
import satori.common.ui.SListPane;
import satori.common.ui.SPane;
import satori.problem.STestSuiteList;
import satori.problem.STestSuiteSnap;

public class STestSuiteListPane implements SPane, SListener1<STestSuiteList> {
	private final SListener0 new_listener;
	private final SListener1<STestSuiteSnap> open_listener;
	
	private STestSuiteList suite_list = null;
	
	private final JButton new_button, open_button;
	private final SListPane<STestSuiteSnap> list;
	private final JComponent pane;
	
	public STestSuiteListPane(SListener0 new_listener, SListener1<STestSuiteSnap> open_listener) {
		this.new_listener = new_listener;
		this.open_listener = open_listener;
		new_button = new JButton("New");
		new_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { newRequest(); }
		});
		open_button = new JButton("Open");
		open_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { openRequest(); }
		});
		JComponent button_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		button_pane.add(new_button);
		button_pane.add(open_button);
		list = new SListPane<STestSuiteSnap>(new Comparator<STestSuiteSnap>() {
			@Override public int compare(STestSuiteSnap ts1, STestSuiteSnap ts2) {
				return ts1.getName().compareTo(ts2.getName());
			}
		}, true);
		list.addColumn(new SListPane.Column<STestSuiteSnap>() {
			@Override public String get(STestSuiteSnap suite) {
				String name = suite.getName();
				return name.isEmpty() ? "(Tests)" : name;
			}
		}, 1.0f);
		list.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
		list.addMouseListener(new MouseAdapter() {
			@Override public void mouseClicked(MouseEvent e) {
				if (e.getClickCount() == 2) { e.consume(); openRequest(); }
			}
		});
		pane = new JPanel(new BorderLayout());
		pane.add(button_pane, BorderLayout.NORTH);
		pane.add(new JScrollPane(list), BorderLayout.CENTER);
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void newRequest() { new_listener.call(); }
	private void openRequest() {
		if (list.isSelectionEmpty()) return;
		open_listener.call(list.getItem(list.getSelectedIndex()));
	}
	
	@Override public void call(STestSuiteList suite_list) {
		if (this.suite_list != null) this.suite_list.removePane(list.getListView());
		this.suite_list = suite_list;
		if (this.suite_list != null) this.suite_list.addPane(list.getListView());
	}
}
