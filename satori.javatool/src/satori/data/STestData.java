package satori.data;

import static satori.data.SAttributeData.convertAttrMap;
import static satori.data.SAttributeData.createBlobs;
import static satori.data.SAttributeData.createLocalAttrMap;
import static satori.data.SAttributeData.createRemoteAttrMap;

import java.util.AbstractList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import satori.metadata.SInputMetadata;
import satori.metadata.SJudge;
import satori.metadata.SJudgeParser;
import satori.session.SSession;
import satori.task.STaskManager;
import satori.test.STestBasicReader;
import satori.test.STestReader;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.Test;
import satori.thrift.gen.TestStruct;

public class STestData {
	static class TestBasicWrap implements STestBasicReader {
		private final TestStruct struct;
		public TestBasicWrap(TestStruct struct) { this.struct = struct; }
		@Override public boolean hasId() { return true; }
		@Override public long getId() { return struct.getId(); }
		@Override public long getProblemId() { return struct.getProblem(); }
		@Override public String getName() { return struct.getName(); }
		@Override public String getDescription() { return struct.getDescription(); }
	}
	static class TestWrap extends TestBasicWrap implements STestReader {
		private final SJudge judge;
		private final Map<SInputMetadata, Object> input;
		public TestWrap(TestStruct struct, Map<String, AnonymousAttribute> data) throws Exception {
			super(struct);
			AnonymousAttribute judge_attr = data.get("judge");
			if (judge_attr == null) {
				judge = null;
				input = Collections.emptyMap();
			} else {
				judge = SJudgeParser.parseJudgeTask(SBlob.createRemote(judge_attr.getFilename(), judge_attr.getValue()));
				input = Collections.unmodifiableMap(createLocalAttrMap(judge.getInputMetadata(), data));
			}
		}
		@Override public SJudge getJudge() { return judge; }
		@Override public Map<SInputMetadata, Object> getInput() { return input; }
	}
	static class TestListWrap extends AbstractList<STestBasicReader> {
		private final List<TestStruct> list;
		public TestListWrap(List<TestStruct> list) { this.list = list; }
		@Override public int size() { return list.size(); }
		@Override public STestBasicReader get(int index) { return new TestBasicWrap(list.get(index)); }
	}
	
	public static STestReader load(long id) throws Exception {
		STaskManager.log("Loading test...");
		Test.Iface iface = new Test.Client(SSession.getProtocol());
		return new TestWrap(iface.Test_get_struct(SSession.getToken(), id), iface.Test_data_get_map(SSession.getToken(), id));
	}
	
	private static TestStruct createStruct(STestBasicReader test) {
		TestStruct struct = new TestStruct();
		struct.setProblem(test.getProblemId());
		struct.setName(test.getName());
		struct.setDescription(test.getDescription());
		return struct;
	}
	
	public static long create(STestReader test) throws Exception {
		Map<String, Object> raw_data = createRemoteAttrMap(test.getInput());
		if (test.getJudge() != null) raw_data.put("judge", test.getJudge().getBlob());
		createBlobs(raw_data);
		STaskManager.log("Creating test...");
		Test.Iface iface = new Test.Client(SSession.getProtocol());
		return iface.Test_create(SSession.getToken(), createStruct(test), convertAttrMap(raw_data)).getId();
	}
	public static void save(STestReader test) throws Exception {
		Map<String, Object> raw_data = createRemoteAttrMap(test.getInput());
		if (test.getJudge() != null) raw_data.put("judge", test.getJudge().getBlob());
		createBlobs(raw_data);
		STaskManager.log("Saving test...");
		Test.Iface iface = new Test.Client(SSession.getProtocol());
		iface.Test_modify_full(SSession.getToken(), test.getId(), createStruct(test), convertAttrMap(raw_data));
	}
	public static void delete(long id) throws Exception {
		STaskManager.log("Deleting test...");
		Test.Iface iface = new Test.Client(SSession.getProtocol());
		iface.Test_delete(SSession.getToken(), id);
	}
	public static List<STestBasicReader> list(long problem_id) throws Exception {
		STaskManager.log("Loading test list...");
		Test.Iface iface = new Test.Client(SSession.getProtocol());
		TestStruct filter = new TestStruct();
		filter.setProblem(problem_id);
		return new TestListWrap(iface.Test_filter(SSession.getToken(), filter));
	}
}
