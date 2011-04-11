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

import satori.common.ui.SListPane;
import satori.common.ui.STabPane;
import satori.common.ui.STabs;
import satori.problem.SProblemList;
import satori.problem.SProblemSnap;
import satori.problem.impl.SProblemImpl;
import satori.task.STaskException;

public class SProblemListPane implements STabPane {
	private final SProblemList problem_list;
	private final STabs parent;
	
	private final JButton new_button, reload_button, close_button;
	private final SListPane<SProblemSnap> list;
	private final JComponent pane;
	
	public SProblemListPane(SProblemList problem_list, STabs parent) {
		this.problem_list = problem_list;
		this.parent = parent;
		new_button = new JButton("New problem");
		new_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { newRequest(); }
		});
		reload_button = new JButton("Reload");
		reload_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { reloadRequest(); }
		});
		close_button = new JButton("Close");
		close_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { closeRequest(); }
		});
		JComponent button_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		button_pane.add(new_button);
		button_pane.add(reload_button);
		button_pane.add(close_button);
		list = new SListPane<SProblemSnap>(new Comparator<SProblemSnap>() {
			@Override public int compare(SProblemSnap p1, SProblemSnap p2) {
				return p1.getName().compareTo(p2.getName());
			}
		}, true);
		list.addColumn(new SListPane.Column<SProblemSnap>() {
			@Override public String get(SProblemSnap problem) {
				String name = problem.getName();
				return name.isEmpty() ? "(Problem)" : name;
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
	
	@Override public boolean hasUnsavedData() { return false; }
	@Override public void close() { problem_list.setPane(null); }
	
	private void newRequest() {
		SProblemImpl problem = SProblemImpl.createNew(problem_list);
		SProblemPane.open(problem, parent);
	}
	private void openRequest() {
		int index = list.getSelectedIndex();
		if (index == -1) return;
		SProblemSnap snap = list.getItem(index);
		SProblemImpl problem = SProblemImpl.createRemote(problem_list, snap);
		try { problem.reload(); }
		catch(STaskException ex) { problem.close(); return; }
		SProblemPane.open(problem, parent);
	}
	private void reloadRequest() {
		try { problem_list.reload(); }
		catch(STaskException ex) {}
	}
	private void closeRequest() {
		close();
		parent.closePane(this);
	}
	
	private static SProblemListPane instance = null;
	
	public static SProblemListPane get(STabs parent) throws STaskException {
		if (instance == null) instance = new SProblemListPane(SProblemList.get(), parent);
		if (!instance.problem_list.hasPane()) instance.problem_list.setPane(instance.list.getListView());
		return instance;
	}
}
