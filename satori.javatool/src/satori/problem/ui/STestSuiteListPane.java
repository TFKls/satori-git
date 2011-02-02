package satori.problem.ui;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

import javax.swing.AbstractListModel;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.ListSelectionModel;

import satori.common.SList;
import satori.common.SView;
import satori.common.ui.SPane;
import satori.problem.STestSuiteSnap;

public class STestSuiteListPane implements SList<STestSuiteSnap>, SPane {
	private final SProblemPane parent;
	
	@SuppressWarnings("serial")
	private static class ListModel extends AbstractListModel implements SView {
		private List<STestSuiteSnap> list = new ArrayList<STestSuiteSnap>();
		private Comparator<STestSuiteSnap> comparator = new Comparator<STestSuiteSnap>() {
			@Override public int compare(STestSuiteSnap ts1, STestSuiteSnap ts2) {
				return ts1.getName().compareTo(ts2.getName());
			}
		};
		
		public STestSuiteSnap getItem(int index) { return list.get(index); }
		public Iterable<STestSuiteSnap> getItems() { return list; }
		
		public void addItem(STestSuiteSnap suite) { list.add(suite); }
		public void removeItem(STestSuiteSnap suite) { list.remove(suite); }
		public void removeAllItems() { list.clear(); }
		
		@Override public void update() {
			Collections.sort(list, comparator);
			fireContentsChanged(this, 0, list.isEmpty() ? 0 : list.size()-1);
		}
		public void updateAfterAdd() {
			Collections.sort(list, comparator);
			fireIntervalAdded(this, 0, list.isEmpty() ? 0 : list.size()-1);
		}
		public void updateAfterRemove() { fireIntervalRemoved(this, 0, list.isEmpty() ? 0 : list.size()-1); }
		
		@Override public String getElementAt(int index) {
			String name = list.get(index).getName();
			return name.isEmpty() ? "(Tests)" : name;
		}
		@Override public int getSize() { return list.size(); }
	}
	
	private ListModel list_model;
	
	private JPanel main_pane;
	private JPanel button_pane;
	private JButton new_button, open_button;
	private JList list;
	private JScrollPane list_pane;
	
	public STestSuiteListPane(SProblemPane parent) {
		this.parent = parent;
		initialize();
	}
	
	@Override public JComponent getPane() { return main_pane; }
	
	private void newRequest() { parent.newTestSuite(); }
	private void openRequest() {
		if (list.isSelectionEmpty()) return;
		parent.openTestSuite(list_model.getItem(list.getSelectedIndex()));
	}
	
	private void initialize() {
		main_pane = new JPanel();
		main_pane.setLayout(new BorderLayout());
		button_pane = new JPanel();
		button_pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		new_button = new JButton("New");
		new_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { newRequest(); }
		});
		button_pane.add(new_button);
		open_button = new JButton("Open");
		open_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { openRequest(); }
		});
		button_pane.add(open_button);
		main_pane.add(button_pane, BorderLayout.NORTH);
		list_model = new ListModel();
		list = new JList(list_model);
		list.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
		list.addMouseListener(new MouseAdapter() {
			@Override public void mouseClicked(MouseEvent e) {
				if (e.getClickCount() == 2) { e.consume(); openRequest(); }
			}
		});
		list_pane = new JScrollPane(list);
		main_pane.add(list_pane, BorderLayout.CENTER);
	}
	
	@Override public void add(STestSuiteSnap suite) {
		list.clearSelection();
		list_model.addItem(suite);
		suite.addView(list_model);
		list_model.updateAfterAdd();
	}
	@Override public void add(Iterable<STestSuiteSnap> suites) {
		list.clearSelection();
		for (STestSuiteSnap ts : suites) {
			list_model.addItem(ts);
			ts.addView(list_model);
		}
		list_model.updateAfterAdd();
	}
	@Override public void remove(STestSuiteSnap suite) {
		list.clearSelection();
		suite.removeView(list_model);
		list_model.removeItem(suite);
		list_model.updateAfterRemove();
	}
	@Override public void removeAll() {
		list.clearSelection();
		for (STestSuiteSnap ts : list_model.getItems()) ts.removeView(list_model);
		list_model.removeAllItems();
		list_model.updateAfterRemove();
	}
}
