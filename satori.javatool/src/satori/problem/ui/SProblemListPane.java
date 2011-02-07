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

import satori.common.SException;
import satori.common.SList;
import satori.common.SView;
import satori.common.ui.STabPane;
import satori.common.ui.STabs;
import satori.main.SFrame;
import satori.problem.SProblemList;
import satori.problem.SProblemSnap;
import satori.problem.impl.SProblemImpl;

public class SProblemListPane implements STabPane, SList<SProblemSnap> {
	private final SProblemList problem_list;
	private final STabs parent;
	
	@SuppressWarnings("serial")
	private static class ListModel extends AbstractListModel implements SView {
		private List<SProblemSnap> list = new ArrayList<SProblemSnap>();
		private Comparator<SProblemSnap> comparator = new Comparator<SProblemSnap>() {
			@Override public int compare(SProblemSnap p1, SProblemSnap p2) {
				return p1.getName().compareTo(p2.getName());
			}
		};
		
		public SProblemSnap getItem(int index) { return list.get(index); }
		public List<SProblemSnap> getItems() { return Collections.unmodifiableList(list); }
		
		public void addItem(SProblemSnap problem) { list.add(problem); }
		public void removeItem(SProblemSnap problem) { list.remove(problem); }
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
			return name.isEmpty() ? "(Problem)" : name;
		}
		@Override public int getSize() { return list.size(); }
	}
	
	private ListModel list_model;
	
	private JPanel main_pane;
	private JPanel button_pane;
	private JButton new_button, reload_button, close_button;
	private JList list;
	private JScrollPane list_pane;
	
	public SProblemListPane(SProblemList problem_list, STabs parent) {
		this.problem_list = problem_list;
		this.parent = parent;
		initialize();
	}
	
	@Override public JComponent getPane() { return main_pane; }
	
	@Override public boolean hasUnsavedData() { return false; }
	@Override public void close() { problem_list.setPane(null); }
	
	private void newRequest() {
		SProblemImpl problem = SProblemImpl.createNew(problem_list);
		SProblemPane.open(problem, parent);
	}
	private void openRequest() {
		int index = list.getSelectedIndex();
		if (index == -1) return;
		SProblemSnap snap = list_model.getItem(index);
		SProblemImpl problem;
		try { problem = SProblemImpl.create(problem_list, snap); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
		SProblemPane.open(problem, parent);
	}
	private void reloadRequest() {
		try { problem_list.load(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void closeRequest() {
		close();
		parent.closePane(this);
	}
	
	private void initialize() {
		main_pane = new JPanel(new BorderLayout());
		button_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		new_button = new JButton("New problem");
		new_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { newRequest(); }
		});
		button_pane.add(new_button);
		reload_button = new JButton("Reload");
		reload_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { reloadRequest(); }
		});
		button_pane.add(reload_button);
		close_button = new JButton("Close");
		close_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { closeRequest(); }
		});
		button_pane.add(close_button);
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
	
	@Override public void add(SProblemSnap problem) {
		list.clearSelection();
		list_model.addItem(problem);
		problem.addView(list_model);
		list_model.updateAfterAdd();
	}
	@Override public void add(Iterable<SProblemSnap> problems) {
		list.clearSelection();
		for (SProblemSnap p : problems) {
			list_model.addItem(p);
			p.addView(list_model);
		}
		list_model.updateAfterAdd();
	}
	@Override public void remove(SProblemSnap problem) {
		list.clearSelection();
		problem.removeView(list_model);
		list_model.removeItem(problem);
		list_model.updateAfterRemove();
	}
	@Override public void removeAll() {
		list.clearSelection();
		for (SProblemSnap p : list_model.getItems()) p.removeView(list_model);
		list_model.removeAllItems();
		list_model.updateAfterRemove();
	}
	
	private static SProblemListPane instance = null;
	
	public static SProblemListPane get(STabs parent) throws SException {
		if (instance == null) instance = new SProblemListPane(SProblemList.get(), parent);
		if (!instance.problem_list.hasPane()) instance.problem_list.setPane(instance);
		return instance;
	}
}
