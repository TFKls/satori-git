package satori.test;

import java.awt.Point;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.event.MouseEvent;
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
import satori.common.SListener2;
import satori.common.ui.SPane;
import satori.common.ui.SScrollPane;
import satori.main.SFrame;
import satori.problem.STestSuiteImpl;
import satori.problem.ui.STestSnapTransfer;

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
	
	private static class MoveTestTransferable implements Transferable {
		private final STestTransfer data;
		public MoveTestTransferable(STestTransfer data) { this.data = data; }
		@Override public DataFlavor[] getTransferDataFlavors() {
			DataFlavor[] flavors = new DataFlavor[1];
			flavors[0] = STestTransfer.flavor;
			return flavors;
		}
		@Override public boolean isDataFlavorSupported(DataFlavor flavor) {
			return flavor.match(STestTransfer.flavor);
		}
		@Override public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, IOException {
			if (flavor.match(STestTransfer.flavor)) return data;
			else throw new UnsupportedFlavorException(flavor);
		}
	}
	private class TestTransferHandler extends TransferHandler implements SListener2<STestImpl, MouseEvent> {
		private STestImpl test;
		
		@Override public boolean canImport(TransferSupport support) {
			if ((support.getSourceDropActions() & COPY) != COPY) return false;
			support.setDropAction(COPY);
			if (support.isDataFlavorSupported(STestSnapTransfer.flavor)) return true;
			if (support.isDataFlavorSupported(STestTransfer.flavor)) {
				Transferable t = support.getTransferable();
				STestTransfer data;
				try { data = (STestTransfer)t.getTransferData(STestTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				return data.getTestSuite() == suite;
			}
			return false;
		}
		@Override public boolean importData(TransferSupport support) {
			if (!support.isDrop()) return false;
			Transferable t = support.getTransferable();
			if (support.isDataFlavorSupported(STestSnapTransfer.flavor)) {
				STestSnapTransfer data;
				try { data = (STestSnapTransfer)t.getTransferData(STestSnapTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				List<STestImpl> new_tests = new ArrayList<STestImpl>();
				for (STestSnap snap : data.get()) {
					if (suite.hasTest(snap.getId())) continue;
					try { new_tests.add(factory.create(snap)); }
					catch(SException ex) { SFrame.showErrorDialog(ex); return false; }
				}
				Point pos = support.getDropLocation().getDropPoint();
				int index = (int)Math.round((pos.getX()-120)/120);
				if (index < 0) index = 0;
				if (index > tests.size()) index = tests.size();
				int cur_index = index;
				for (STestImpl test : new_tests) suite.addTest(test, cur_index++);
				add(new_tests, index);
				return true;
			}
			else if (support.isDataFlavorSupported(STestTransfer.flavor)) {
				STestTransfer data;
				try { data = (STestTransfer)t.getTransferData(STestTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				if (data.getTestSuite() != suite) return false;
				STestImpl test = data.getTest();
				Point pos = support.getDropLocation().getDropPoint();
				int index = (int)Math.round((pos.getX()-120)/120);
				if (index < 0) index = 0;
				if (index > tests.size()) index = tests.size();
				suite.moveTest(test, index);
				move(test, index);
				return true;
			}
			else return false;
		}
		@Override protected Transferable createTransferable(JComponent c) {
			return new MoveTestTransferable(new STestTransfer(test, suite));
		}
		@Override public int getSourceActions(JComponent c) { return COPY; }
		@Override protected void exportDone(JComponent source, Transferable data, int action) {}
		@Override public void call(STestImpl test, MouseEvent e) {
			this.test = test;
			exportAsDrag(scroll_pane.getPane(), e, TransferHandler.COPY);
		}
	}
	private TestTransferHandler transfer_handler = new TestTransferHandler();
	
	public STestPane(TestCaseMetadata meta, STestSuiteImpl suite, STestFactory factory) {
		this.meta = meta;
		this.suite = suite;
		this.factory = factory;
		initialize();
	}
	
	@Override public JComponent getPane() { return scroll_pane.getPane(); }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new BoxLayout(pane, BoxLayout.Y_AXIS));
		addRow(new SGenericRowView("Status", new SStatusItemView.Factory()));
		addRow(new SButtonRowView(new SButtonItemView.Factory(transfer_handler, close_test_listener), new_test_listener));
		addRow(new SGenericRowView("Test name", new SInfoItemView.Factory()));
		meta.createTestPane(this);
		
		scroll_pane = new SScrollPane();
		scroll_pane.setView(pane);
		scroll_pane.getPane().setTransferHandler(transfer_handler);
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
	public void add(Iterable<STestImpl> tests, int index) {
		for (STestImpl test : tests) {
			this.tests.add(index, test);
			addColumn(test, index++);
		}
		pane.revalidate(); pane.repaint();
	}
	@Override public void add(Iterable<STestImpl> tests) {
		add(tests, this.tests.size());
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
	public void move(STestImpl test, int index) {
		int old_index = tests.indexOf(test);
		removeColumn(old_index);
		tests.remove(test);
		if (old_index < index) --index;
		tests.add(index, test);
		addColumn(test, index);
		pane.revalidate(); pane.repaint();
	}
}
