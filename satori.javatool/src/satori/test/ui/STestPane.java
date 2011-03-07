package satori.test.ui;

import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.Graphics;
import java.awt.Insets;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.dnd.DropTargetDragEvent;
import java.awt.dnd.DropTargetDropEvent;
import java.awt.dnd.DropTargetEvent;
import java.awt.dnd.DropTargetListener;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;
import java.awt.event.MouseEvent;
import java.awt.event.MouseMotionListener;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TooManyListenersException;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.TransferHandler;

import satori.blob.SBlob;
import satori.common.SException;
import satori.common.SList;
import satori.common.SListener0;
import satori.common.SListener1;
import satori.common.SView;
import satori.common.ui.SBlobInputView;
import satori.common.ui.SPaneView;
import satori.common.ui.SPane;
import satori.common.ui.SScrollPane;
import satori.common.ui.SStringInputView;
import satori.main.SFrame;
import satori.metadata.SInputMetadata;
import satori.metadata.SJudge;
import satori.problem.impl.STestSuiteImpl;
import satori.test.STestSnap;
import satori.test.impl.SBlobInput;
import satori.test.impl.SJudgeInput;
import satori.test.impl.SSolution;
import satori.test.impl.SStringInput;
import satori.test.impl.STestFactory;
import satori.test.impl.STestImpl;
import satori.thrift.SGlobalData;
import satori.type.SBlobType;

public class STestPane implements SPane, SList<STestImpl> {
	private final STestSuiteImpl suite;
	private final STestFactory factory;
	
	private List<SSolutionPane> solution_panes = new ArrayList<SSolutionPane>();
	private List<STestImpl> tests = new ArrayList<STestImpl>();
	private List<SView> parent_views = new ArrayList<SView>();
	
	private JComponent pane;
	private JComponent input_pane;
	private SScrollPane scroll_pane;
	
	private SListener1<SSolutionPane> remove_solution_listener = new SListener1<SSolutionPane>() {
		@Override public void call(SSolutionPane removed_pane) {
			removeSolutionPane(removed_pane);
		}
	};
	
	private int indicator_index = -1;
	private Rectangle indicator_rect = null;
	private boolean accept_drop = false;
	
	private int getDropIndex(Point location) {
		int index = (int)Math.round((location.getX() - SDimension.labelWidth) / SDimension.itemWidth);
		if (index < 0) index = 0;
		if (index > tests.size()) index = tests.size();
		return index;
	}
	private void indicateDrop(Point location) {
		int index = location != null && accept_drop ? getDropIndex(location) : -1;
		if (index == indicator_index) return;
		indicator_index = index;
		if (indicator_rect != null) {
			input_pane.repaint(indicator_rect);
			indicator_rect = null;
		}
		if (index == -1) return;
		int x = SDimension.labelWidth + index * SDimension.itemWidth - 1;
		int height = input_pane.getHeight();
		indicator_rect = new Rectangle(x, 0, 1, height);
		input_pane.repaint(indicator_rect);
	}
	
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
	@SuppressWarnings("serial")
	private class TestTransferHandler extends TransferHandler {
		private STestImpl test;
		public void setTest(STestImpl test) { this.test = test; }
		@Override public boolean canImport(TransferSupport support) {
			if (!support.isDrop()) return false;
			accept_drop = false;
			if (support.isDataFlavorSupported(STestSnapTransfer.flavor)) {
				if ((support.getSourceDropActions() & COPY) != COPY) return false;
				support.setDropAction(COPY);
				accept_drop = true;
				return true;
			}
			if (support.isDataFlavorSupported(STestTransfer.flavor)) {
				if ((support.getSourceDropActions() & MOVE) != MOVE) return false;
				support.setDropAction(MOVE);
				Transferable t = support.getTransferable();
				STestTransfer data;
				try { data = (STestTransfer)t.getTransferData(STestTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				if (data.getTestSuite() != suite) return false;
				accept_drop = true;
				return true;
			}
			return false;
		}
		@Override public boolean importData(TransferSupport support) {
			if (!support.isDrop()) return false;
			accept_drop = false;
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
				int index = getDropIndex(support.getDropLocation().getDropPoint());
				int cur_index = index;
				for (STestImpl test : new_tests) suite.addTest(test, cur_index++);
				add(new_tests, index);
				return true;
			}
			if (support.isDataFlavorSupported(STestTransfer.flavor)) {
				STestTransfer data;
				try { data = (STestTransfer)t.getTransferData(STestTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				if (data.getTestSuite() != suite) return false;
				STestImpl test = data.getTest();
				int index = getDropIndex(support.getDropLocation().getDropPoint());
				suite.moveTest(test, index);
				move(test, index);
				return true;
			}
			return false;
		}
		@Override protected Transferable createTransferable(JComponent c) {
			return new MoveTestTransferable(new STestTransfer(test, suite));
		}
		@Override public int getSourceActions(JComponent c) { return MOVE; }
		@Override protected void exportDone(JComponent source, Transferable data, int action) {}
	}
	private TestTransferHandler transfer_handler = new TestTransferHandler();
	
	private DropTargetListener drop_listener = new DropTargetListener() {
		@Override public void dragEnter(DropTargetDragEvent e) { indicateDrop(e.getLocation()); }
		@Override public void dragOver(DropTargetDragEvent e) { indicateDrop(e.getLocation()); }
		@Override public void dragExit(DropTargetEvent e) { indicateDrop(null); }
		@Override public void drop(DropTargetDropEvent e) { indicateDrop(null); }
		@Override public void dropActionChanged(DropTargetDragEvent e) { indicateDrop(e.getLocation()); }
	};
	
	public STestPane(STestSuiteImpl suite, STestFactory factory) {
		this.suite = suite;
		this.factory = factory;
		initialize();
	}
	
	@Override public JComponent getPane() { return scroll_pane.getPane(); }
	
	@SuppressWarnings("serial")
	private class Pane extends Box {
		public Pane() { super(BoxLayout.Y_AXIS); }
		@Override public void paint(Graphics g) {
			super.paint(g);
			if (indicator_rect == null) return;
			g.setColor(Color.BLUE);
			g.fillRect(indicator_rect.x, indicator_rect.y, indicator_rect.width, indicator_rect.height);
		}
	}
	
	private void addNewTestRequest() {
		STestImpl test = factory.createNew();
		suite.addTest(test);
		add(test);
	}
	private void saveTestRequest(STestImpl test) {
		if (!test.isProblemRemote()) { SFrame.showErrorDialog("Cannot save: the problem does not exist remotely"); return; }
		try { if (test.isRemote()) test.save(); else test.create(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void saveAllTestsRequest() {
		if (!suite.isProblemRemote()) { SFrame.showErrorDialog("Cannot save: the problem does not exist remotely"); return; }
		for (STestImpl test : suite.getTests()) {
			try { if (test.isRemote()) test.save(); else test.create(); }
			catch(SException ex) { SFrame.showErrorDialog(ex); return; }
		}
	}
	private void reloadTestRequest(STestImpl test) {
		if (!test.isRemote()) return;
		try { test.reload(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void reloadAllTestsRequest() {
		for (STestImpl test : suite.getTests()) {
			if (!test.isRemote()) continue;
			try { test.reload(); }
			catch(SException ex) { SFrame.showErrorDialog(ex); return; }
		}
	}
	private void deleteTestRequest(STestImpl test) {
		if (!test.isRemote()) return;
		if (!SFrame.showWarningDialog("The test will be deleted.")) return;
		try { test.delete(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void removeTestRequest(STestImpl test) {
		if (test.isModified() && !SFrame.showWarningDialog("The test contains unsaved data.")) return;
		remove(test);
		suite.removeTest(test);
	}
	private void moveTestRequest(STestImpl test, MouseEvent e) {
		transfer_handler.setTest(test);
		transfer_handler.exportAsDrag(scroll_pane.getPane(), e, TransferHandler.MOVE);
	}
	
//
//  ButtonItem
//
	private class ButtonItem implements SPane {
		private final STestImpl test;
		
		private JComponent pane;
		
		public ButtonItem(STestImpl test) {
			this.test = test;
			initialize();
		}
		
		@Override public JComponent getPane() { return pane; }
		
		private void initialize() {
			pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
			SDimension.setButtonItemSize(pane);
			final JButton move_button = new JButton(SIcons.moveIcon);
			move_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(move_button);
			move_button.setToolTipText("Move");
			move_button.addMouseMotionListener(new MouseMotionListener() {
				@Override public void mouseDragged(MouseEvent e) {
					move_button.getModel().setArmed(false);
					move_button.getModel().setPressed(false);
					move_button.getModel().setRollover(false);
					moveTestRequest(test, e);
				}
				@Override public void mouseMoved(MouseEvent e) {}
			});
			pane.add(move_button);
			final JButton save_button = new JButton(SIcons.saveIcon);
			save_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(save_button);
			save_button.setToolTipText("Save");
			save_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					saveTestRequest(test);
				}
			});
			pane.add(save_button);
			final JButton reload_button = new JButton(SIcons.refreshIcon);
			reload_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(reload_button);
			reload_button.setToolTipText("Reload");
			reload_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					reloadTestRequest(test);
				}
			});
			pane.add(reload_button);
			final JButton delete_button = new JButton(SIcons.trashIcon);
			delete_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(delete_button);
			delete_button.setToolTipText("Delete");
			delete_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					deleteTestRequest(test);
				}
			});
			pane.add(delete_button);
			final JButton remove_button = new JButton(SIcons.removeIcon);
			remove_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(remove_button);
			remove_button.setToolTipText("Remove");
			remove_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					removeTestRequest(test);
				}
			});
			pane.add(remove_button);
		}
	}
	
//
//  ButtonRow
//
	private class ButtonRow implements SRow {
		private JComponent pane;
		
		public ButtonRow() { initialize(); }
		
		@Override public JComponent getPane() { return pane; }
		
		private void initialize() {
			pane = new Box(BoxLayout.X_AXIS);
			JPanel label_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
			SDimension.setButtonLabelSize(label_pane);
			JButton save_button = new JButton(SIcons.saveIcon);
			save_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(save_button);
			save_button.setToolTipText("Save all");
			save_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					saveAllTestsRequest();
				}
			});
			label_pane.add(save_button);
			JButton reload_button = new JButton(SIcons.refreshIcon);
			reload_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(reload_button);
			reload_button.setToolTipText("Reload all");
			reload_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					reloadAllTestsRequest();
				}
			});
			label_pane.add(reload_button);
			pane.add(label_pane);
			JButton add_button = new JButton(SIcons.addIcon);
			add_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(add_button);
			add_button.setToolTipText("Add new test");
			add_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) { addNewTestRequest(); }
			});
			pane.add(add_button);
			pane.add(Box.createHorizontalGlue());
		}
		
		@Override public void addColumn(STestImpl test, int index) {
			int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
			pane.add(new ButtonItem(test).getPane(), pane_index);
		}
		@Override public void removeColumn(int index) {
			pane.remove(index+1);
		}
	};
	
//
//  StatusItem
//
	private class StatusItem implements SPane, SView {
		private final STestImpl test;
		
		private JLabel label;
		
		public StatusItem(STestImpl test) {
			this.test = test;
			test.addView(this);
			initialize();
		}
		
		@Override public JComponent getPane() { return label; }
		
		private void initialize() {
			label = new JLabel();
			SDimension.setItemSize(label);
			update();
		}
		
		@Override public void update() {
			String status_text = "";
			if (test.isRemote()) {
				if (test.isOutdated()) status_text = "outdated";
			} else {
				if (test.isOutdated()) status_text = "deleted";
				else status_text = "new";
			}
			if (test.isModified()) {
				if (!status_text.isEmpty()) status_text += ", ";
				status_text += "modified";
			}
			if (status_text.isEmpty()) status_text = "saved";
			label.setText(status_text);
		}
	}
	
//
//  StatusRow
//
	private class StatusRow implements SRow {
		private JComponent pane;
		
		public StatusRow() { initialize(); }
		
		@Override public JComponent getPane() { return pane; }
		
		private void initialize() {
			pane = new Box(BoxLayout.X_AXIS);
			JLabel label = new JLabel("Status");
			SDimension.setLabelSize(label);
			pane.add(label);
			pane.add(Box.createHorizontalGlue());
		}
		
		@Override public void addColumn(STestImpl test, int index) {
			int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
			pane.add(new StatusItem(test).getPane(), pane_index);
		}
		@Override public void removeColumn(int index) {
			pane.remove(index+1);
		}
	}
	
//
//  InfoItem
//
	private class InfoItem implements SPane, SView {
		private final STestImpl test;
		
		private JComponent pane;
		private JTextField name_field;
		private JTextField desc_field;
		
		public InfoItem(STestImpl test) {
			this.test = test;
			test.addView(this);
			initialize();
		}
		
		@Override public JComponent getPane() { return pane; }
		
		private void updateName() { test.setName(name_field.getText()); }
		private void updateDescription() { test.setDescription(desc_field.getText()); }
		
		private void initialize() {
			pane = new Box(BoxLayout.Y_AXIS);
			name_field = new JTextField();
			SDimension.setItemSize(name_field);
			name_field.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) { updateName(); }
			});
			name_field.addFocusListener(new FocusListener() {
				@Override public void focusGained(FocusEvent e) {}
				@Override public void focusLost(FocusEvent e) { updateName(); }
			});
			pane.add(name_field);
			desc_field = new JTextField();
			SDimension.setItemSize(desc_field);
			desc_field.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) { updateDescription(); }
			});
			desc_field.addFocusListener(new FocusListener() {
				@Override public void focusGained(FocusEvent e) {}
				@Override public void focusLost(FocusEvent e) { updateDescription(); }
			});
			pane.add(desc_field);
			SBlobInputView judge_view = new SBlobInputView(new SJudgeInput(test), new SBlobInputView.BlobLoader() {
				private Map<String, SBlob> blobs = null;
				@Override public Map<String, SBlob> getBlobs() throws SException {
					if (blobs == null) blobs = SGlobalData.getJudges();
					return blobs;
				}
			});
			test.addView(judge_view);
			judge_view.getPane().setPreferredSize(SDimension.itemDim);
			judge_view.getPane().setMinimumSize(SDimension.itemDim);
			judge_view.getPane().setMaximumSize(SDimension.itemDim);
			pane.add(judge_view.getPane());
			update();
		}
		
		@Override public void update() {
			name_field.setText(test.getName());
			desc_field.setText(test.getDescription());
		}
	}
	
//
//  InfoRow
//
	private class InfoRow implements SRow {
		private JComponent pane;
		
		public InfoRow() { initialize(); }
		
		@Override public JComponent getPane() { return pane; }
		
		private void initialize() {
			pane = new Box(BoxLayout.X_AXIS);
			JLabel name_label = new JLabel("Name");
			SDimension.setLabelSize(name_label);
			JLabel desc_label = new JLabel("Description");
			SDimension.setLabelSize(desc_label);
			JLabel judge_label = new JLabel("Judge");
			SDimension.setLabelSize(judge_label);
			Box label_box = new Box(BoxLayout.Y_AXIS);
			label_box.add(name_label);
			label_box.add(desc_label);
			label_box.add(judge_label);
			pane.add(label_box);
			pane.add(Box.createHorizontalGlue());
		}
		
		@Override public void addColumn(STestImpl test, int index) {
			int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
			pane.add(new InfoItem(test).getPane(), pane_index);
		}
		@Override public void removeColumn(int index) {
			pane.remove(index+1);
		}
	}
	
//
//  DataItem
//
	private class DataItem implements SPane {
		private final STestImpl test;
		
		private JComponent pane;
		
		public DataItem(STestImpl test) {
			this.test = test;
			initialize();
		}
		
		@Override public JComponent getPane() { return pane; }
		
		private void fillPane() {
			SJudge judge = test.getJudge();
			if (judge != null) for (SInputMetadata im : judge.getInputMetadata()) {
				SPaneView view;
				if (im.getType() == SBlobType.INSTANCE) view = new SBlobInputView(new SBlobInput(im, test));
				else view = new SStringInputView(new SStringInput(im, test));
				test.addView(view);
				view.getPane().setPreferredSize(SDimension.itemDim);
				view.getPane().setMinimumSize(SDimension.itemDim);
				view.getPane().setMaximumSize(SDimension.itemDim);
				pane.add(view.getPane());
			}
			pane.add(Box.createVerticalGlue());
		}
		private void initialize() {
			pane = new Box(BoxLayout.Y_AXIS);
			fillPane();
			test.addMetadataModifiedListener(new SListener0() {
				@Override public void call() {
					pane.removeAll();
					fillPane();
					pane.revalidate(); pane.repaint();
				}
			});
		}
	}
	
//
//  DataRow
//
	private class DataRow implements SRow {
		private JComponent pane;
		
		public DataRow() { initialize(); }
		
		@Override public JComponent getPane() { return pane; }
		
		private void initialize() {
			pane = new Box(BoxLayout.X_AXIS);
			JLabel label = new JLabel("Data");
			SDimension.setLabelSize(label);
			Box label_box = new Box(BoxLayout.Y_AXIS);
			label_box.add(label);
			label_box.add(Box.createVerticalGlue());
			pane.add(label_box);
			pane.add(Box.createHorizontalGlue());
		}
		
		@Override public void addColumn(STestImpl test, int index) {
			int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
			pane.add(new DataItem(test).getPane(), pane_index);
		}
		@Override public void removeColumn(int index) {
			pane.remove(index+1);
		}
	}
	
//
//  Input pane
//
	private List<SRow> input_rows = new ArrayList<SRow>();
	
	private void addInputRow(SRow row) {
		input_rows.add(row);
		input_pane.add(row.getPane());
	}
	private void addInputColumn(STestImpl test, int index) {
		for (SRow row : input_rows) row.addColumn(test, index);
	}
	private void removeInputColumn(int index) {
		for (SRow row : input_rows) row.removeColumn(index);
	}
	
//
//  Solution panes
//
	private void addSolutionPane() {
		SSolution solution = new SSolution();
		SSolutionPane new_pane = new SSolutionPane(solution, remove_solution_listener);
		pane.add(new_pane.getPane(), solution_panes.size()+1);
		solution_panes.add(new_pane);
		int index = 0;
		for (STestImpl test : tests) new_pane.addColumn(test, index++);
		pane.revalidate(); pane.repaint();
	}
	private void removeSolutionPane(SSolutionPane removed_pane) {
		for (int index = tests.size()-1; index >= 0; --index) removed_pane.removeColumn(index);
		pane.remove(solution_panes.indexOf(removed_pane)+1);
		solution_panes.remove(removed_pane);
		pane.revalidate(); pane.repaint();
	}
	
	private void initialize() {
		pane = new Pane();
		input_pane = new Box(BoxLayout.Y_AXIS);
		addInputRow(new StatusRow());
		addInputRow(new ButtonRow());
		addInputRow(new InfoRow());
		addInputRow(new DataRow());
		pane.add(input_pane);
		JPanel bottom_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		JButton bottom_button = new JButton("Add solution");
		bottom_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonHeight(bottom_button);
		bottom_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				addSolutionPane();
			}
		});
		bottom_pane.add(bottom_button);
		pane.add(bottom_pane);
		scroll_pane = new SScrollPane();
		scroll_pane.setView(pane);
		scroll_pane.getPane().setTransferHandler(transfer_handler);
		try { scroll_pane.getPane().getDropTarget().addDropTargetListener(drop_listener); }
		catch(TooManyListenersException ex) {}
	}
	
	private void addColumn(STestImpl test, int index) {
		addInputColumn(test, index);
		for (SRow pane : solution_panes) pane.addColumn(test, index);
	}
	private void removeColumn(int index) {
		removeInputColumn(index);
		for (SRow pane : solution_panes) pane.removeColumn(index);
	}
	
	@Override public void add(STestImpl test) {
		int index = tests.size();
		tests.add(test);
		addParentViews(test);
		addColumn(test, index);
		pane.revalidate(); pane.repaint();
	}
	public void add(Iterable<STestImpl> tests, int index) {
		for (STestImpl test : tests) {
			this.tests.add(index, test);
			addParentViews(test);
			addColumn(test, index++);
		}
		pane.revalidate(); pane.repaint();
	}
	@Override public void add(Iterable<STestImpl> tests) {
		add(tests, this.tests.size());
	}
	@Override public void remove(STestImpl test) {
		test.close();
		removeColumn(tests.indexOf(test));
		tests.remove(test);
		pane.revalidate(); pane.repaint();
	}
	@Override public void removeAll() {
		for (STestImpl test : tests) test.close();
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
	
	public boolean hasUnsavedData() {
		for (STestImpl test : tests) if (test.isModified()) return true;
		return false;
	}
	
	public void addParentView(SView view) {
		for (STestImpl test : tests) test.addView(view);
		parent_views.add(view);
	}
	public void removeParentView(SView view) {
		parent_views.remove(view);
		for (STestImpl test : tests) test.removeView(view);
	}
	private void addParentViews(STestImpl test) {
		for (SView view : parent_views) test.addView(view);
	}
}
