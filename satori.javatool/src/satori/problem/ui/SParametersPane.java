package satori.problem.ui;

import java.awt.Dimension;
import java.util.List;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JLabel;

import satori.common.SInput;
import satori.common.SListener0;
import satori.common.ui.SBlobInputView;
import satori.common.ui.SPane;
import satori.common.ui.SPaneView;
import satori.common.ui.SStringInputView;
import satori.data.SBlob;
import satori.metadata.SInputMetadata;
import satori.metadata.SParametersMetadata;
import satori.problem.impl.STestSuiteImpl;
import satori.type.SBlobType;

public class SParametersPane implements SPane {
	private static final int itemHeight = 20;
	private static final int labelWidth = 206;
	private static final int itemWidth = 111;
	private static final Dimension labelDim = new Dimension(labelWidth, itemHeight);
	private static final Dimension itemDim = new Dimension(itemWidth, itemHeight);
	
	private final STestSuiteImpl suite;
	
	private JComponent pane;
	
	public SParametersPane(STestSuiteImpl suite) {
		this.suite = suite;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private static class BlobInput implements SInput<SBlob> {
		private final SInputMetadata meta;
		private final STestSuiteImpl suite;
		
		public BlobInput(SInputMetadata meta, STestSuiteImpl suite) {
			this.meta = meta;
			this.suite = suite;
		}
		
		@Override public SBlob get() { return (SBlob)suite.getGeneralParameter(meta); }
		@Override public String getText() {
			SBlob data = get();
			return data != null ? data.getName() : null;
		}
		@Override public String getDescription() { return null; }
		@Override public boolean isValid() {
			SBlob data = get();
			return data != null ? meta.getType().isValid(data) : !meta.isRequired();
		}
		@Override public void set(SBlob data) { suite.setGeneralParameter(meta, data); }
	}
	public class StringInput implements SInput<String> {
		private final SInputMetadata meta;
		private final STestSuiteImpl suite;
		
		public StringInput(SInputMetadata meta, STestSuiteImpl suite) {
			this.meta = meta;
			this.suite = suite;
		}
		
		@Override public String get() { return (String)suite.getGeneralParameter(meta); }
		@Override public String getText() { return get(); }
		@Override public String getDescription() { return null; }
		@Override public boolean isValid() {
			String data = get();
			return data != null ? meta.getType().isValid(data) : !meta.isRequired();
		}
		@Override public void set(String data) { suite.setGeneralParameter(meta, data); }
	}
	
	private void fillPane(String name, List<SInputMetadata> meta) {
		if (meta.isEmpty()) return;
		JLabel top_label = new JLabel(name + " parameters:");
		top_label.setAlignmentX(0.0f);
		pane.add(top_label);
		for (SInputMetadata im : meta) {
			Box row = new Box(BoxLayout.X_AXIS);
			row.setAlignmentX(0.0f);
			JLabel label = new JLabel(im.getDescription());
			label.setPreferredSize(labelDim);
			label.setMinimumSize(labelDim);
			label.setMaximumSize(labelDim);
			row.add(label);
			SPaneView view;
			if (im.getType() == SBlobType.INSTANCE) view = new SBlobInputView(new BlobInput(im, suite));
			else view = new SStringInputView(new StringInput(im, suite));
			suite.addView(view);
			view.getPane().setPreferredSize(itemDim);
			view.getPane().setMinimumSize(itemDim);
			view.getPane().setMaximumSize(itemDim);
			row.add(view.getPane());
			pane.add(row);
		}
	}
	private void fillPane() {
		if (suite.getDispatcher() != null) fillPane(suite.getDispatcher().getName(), suite.getDispatcher().getGeneralParameters());
		for (SParametersMetadata pm : suite.getAccumulators()) fillPane(pm.getName(), pm.getGeneralParameters());
		if (suite.getReporter() != null) fillPane(suite.getReporter().getName(), suite.getReporter().getGeneralParameters());
	}
	private void initialize() {
		pane = new Box(BoxLayout.Y_AXIS);
		fillPane();
		suite.addMetadataModifiedListener(new SListener0() {
			@Override public void call() {
				pane.removeAll();
				fillPane();
				pane.revalidate(); pane.repaint();
			}
		});
	}
}
