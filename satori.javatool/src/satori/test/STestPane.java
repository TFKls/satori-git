package satori.test;

import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JPanel;
import javax.swing.TransferHandler;

import satori.common.SException;
import satori.common.SList;
import satori.common.SListener;
import satori.common.ui.SPane;
import satori.common.ui.SScrollPane;
import satori.main.SFrame;
import satori.problem.STestSuiteImpl;
import satori.problem.ui.STestTransfer;

public class STestPane implements SList<STestImpl>, SPane {
	private final TestCaseMetadata meta;
	private final STestSuiteImpl suite;
	private final STestFactory factory;
	
	private List<SRowView> rows = new ArrayList<SRowView>();
	private List<STestImpl> tests = new ArrayList<STestImpl>();
	
	private JPanel pane;
	private SScrollPane scroll_pane;
	
	private SListener<STestImpl> new_test_listener = new SListener<STestImpl>() {
		@Override public void call(STestImpl unused) {
			STestImpl test = factory.createNew();
			suite.addTest(test);
			add(test);
		}
	};
	private SListener<STestImpl> close_test_listener = new SListener<STestImpl>() {
		@Override public void call(STestImpl test) {
			remove(test);
			suite.removeTest(test);
		}
	};
	
	public STestPane(TestCaseMetadata meta, STestSuiteImpl suite, STestFactory factory) {
		this.meta = meta;
		this.suite = suite;
		this.factory = factory;
		initialize();
	}
	
	@Override public JComponent getPane() { return scroll_pane.getPane(); }
	
	private class TestTransferHandler extends TransferHandler {
		@Override public boolean canImport(TransferSupport support) {
			if ((support.getSourceDropActions() & COPY) != COPY) return false;
			support.setDropAction(COPY);
			return support.isDataFlavorSupported(STestTransfer.flavor);
		}
		@Override public boolean importData(TransferSupport support) {
			if (!support.isDrop()) return false;
			Transferable t = support.getTransferable();
			STestTransfer data;
			try { data = (STestTransfer)t.getTransferData(STestTransfer.flavor); }
			catch(UnsupportedFlavorException ex) { return false; }
			catch(IOException ex) { return false; }
			List<STestImpl> tests = new ArrayList<STestImpl>();
			for (STestSnap snap : data.getTests()) {
				if (suite.hasTest(snap.getId())) continue;
				try { tests.add(factory.create(snap)); }
				catch(SException ex) { SFrame.showErrorDialog(ex); return false; }
			}
			for (STestImpl test : tests) suite.addTest(test);
			add(tests);
			return true;
		}
	}
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new BoxLayout(pane, BoxLayout.Y_AXIS));
		addRow(new SGenericRowView("Status", new SStatusItemView.Factory()));
		addRow(new SButtonRowView(new SButtonItemView.Factory(close_test_listener), new_test_listener));
		addRow(new SGenericRowView("Test name", new SInfoItemView.Factory()));
		meta.createTestPane(this);
		
		scroll_pane = new SScrollPane();
		scroll_pane.setView(pane);
		scroll_pane.getPane().setTransferHandler(new TestTransferHandler());
	}
	
	public void addRow(SRowView row) {
		rows.add(row);
		pane.add(row.getPane());
	}
	
	private void addColumn(STestImpl test, int index) {
		for (SRowView row : rows) row.addColumn(test, index);
	}
	private void removeColumn(int index) {
		for (SRowView row : rows) row.removeColumn(index);
	}
	
	@Override public void add(STestImpl test) {
		int index = tests.size();
		tests.add(test);
		addColumn(test, index);
		pane.revalidate(); pane.repaint();
	}
	@Override public void add(Iterable<STestImpl> tests) {
		int index = this.tests.size();
		for (STestImpl test : tests) {
			this.tests.add(test);
			addColumn(test, index++);
		}
		pane.revalidate(); pane.repaint();
	}
	@Override public void remove(STestImpl test) {
		removeColumn(tests.indexOf(test));
		tests.remove(test);
		pane.revalidate(); pane.repaint();
	}
	@Override public void removeAll() {
		for (int i = tests.size()-1; i >= 0; --i) removeColumn(i);
		tests.clear();
		pane.revalidate(); pane.repaint();
	}
}
