package satori.thrift;

import static satori.thrift.SAttributeData.convertAttrMap;
import static satori.thrift.SAttributeData.createBlobs;
import static satori.thrift.SAttributeData.createLocalAttrMap;
import static satori.thrift.SAttributeData.createRemoteAttrMap;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import satori.blob.SBlob;
import satori.common.SException;
import satori.metadata.SInputMetadata;
import satori.metadata.SJudge;
import satori.metadata.SJudgeParser;
import satori.session.SSession;
import satori.test.STestBasicReader;
import satori.test.STestReader;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.Test;
import satori.thrift.gen.TestStruct;

public class STestData {
	static class TestBasicWrap implements STestBasicReader {
		private TestStruct struct;
		public TestBasicWrap(TestStruct struct) { this.struct = struct; }
		@Override public boolean hasId() { return true; }
		@Override public long getId() { return struct.getId(); }
		@Override public long getProblemId() { return struct.getProblem(); }
		@Override public String getName() { return struct.getName(); }
	}
	static class TestWrap extends TestBasicWrap implements STestReader {
		private final SJudge judge;
		private final Map<SInputMetadata, Object> input;
		public TestWrap(TestStruct struct, Map<String, AnonymousAttribute> data) throws SException {
			super(struct);
			AnonymousAttribute judge_attr = data.get("judge");
			if (judge_attr == null) {
				judge = null;
				input = Collections.emptyMap();
			} else {
				judge = SJudgeParser.parseJudge(SBlob.createRemote(judge_attr.getFilename(), judge_attr.getValue()));
				input = Collections.unmodifiableMap(createLocalAttrMap(judge.getInputMetadata(), data));
			}
		}
		@Override public SJudge getJudge() { return judge; }
		@Override public Map<SInputMetadata, Object> getInput() { return input; }
	}
	
	static List<STestBasicReader> createTestList(List<TestStruct> structs) {
		List<STestBasicReader> tests = new ArrayList<STestBasicReader>();
		for (TestStruct struct : structs) tests.add(new TestBasicWrap(struct));
		return Collections.unmodifiableList(tests);
	}
	
	private static class LoadCommand implements SThriftCommand {
		private final long id;
		private TestStruct test;
		private Map<String, AnonymousAttribute> data;
		public TestStruct getTest() { return test; }
		public Map<String, AnonymousAttribute> getData() { return data; }
		public LoadCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			test = iface.Test_get_struct(SSession.getToken(), id);
			data = iface.Test_data_get_map(SSession.getToken(), id);
		}
	}
	public static STestReader load(long id) throws SException {
		LoadCommand command = new LoadCommand(id);
		SThriftClient.call(command);
		return new TestWrap(command.getTest(), command.getData());
	}
	
	private static TestStruct createStruct(STestBasicReader test) {
		TestStruct struct = new TestStruct();
		struct.setProblem(test.getProblemId());
		struct.setName(test.getName());
		return struct;
	}
	
	private static class CreateCommand implements SThriftCommand {
		private final TestStruct test;
		private final Map<String, AnonymousAttribute> data;
		private long result;
		public long getResult() { return result; }
		public CreateCommand(TestStruct test, Map<String, AnonymousAttribute> data) {
			this.test = test;
			this.data = data;
		}
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			result = iface.Test_create(SSession.getToken(), test, data).getId();
		}
	}
	public static long create(STestReader test) throws SException {
		Map<String, Object> raw_data = createRemoteAttrMap(test.getInput());
		if (test.getJudge() != null) raw_data.put("judge", test.getJudge().getBlob());
		createBlobs(raw_data);
		CreateCommand command = new CreateCommand(createStruct(test), convertAttrMap(raw_data));
		SThriftClient.call(command);
		return command.getResult();
	}
	
	private static class SaveCommand implements SThriftCommand {
		private final long id;
		private final TestStruct test;
		private final Map<String, AnonymousAttribute> data;
		public SaveCommand(long id, TestStruct test, Map<String, AnonymousAttribute> data) {
			this.id = id;
			this.test = test;
			this.data = data;
		}
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			iface.Test_modify_full(SSession.getToken(), id, test, data);
		}
	}
	public static void save(STestReader test) throws SException {
		Map<String, Object> raw_data = createRemoteAttrMap(test.getInput());
		if (test.getJudge() != null) raw_data.put("judge", test.getJudge().getBlob());
		createBlobs(raw_data);
		SThriftClient.call(new SaveCommand(test.getId(), createStruct(test), convertAttrMap(raw_data)));
	}
	
	private static class DeleteCommand implements SThriftCommand {
		private final long id;
		public DeleteCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			iface.Entity_delete(SSession.getToken(), id);
		}
	}
	public static void delete(long id) throws SException {
		SThriftClient.call(new DeleteCommand(id));
	}
	
	private static class ListCommand implements SThriftCommand {
		private final long problem_id;
		private List<TestStruct> list;
		public ListCommand(long problem_id) { this.problem_id = problem_id; }
		public List<TestStruct> getList() { return list; }
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			TestStruct filter = new TestStruct();
			filter.setProblem(problem_id);
			list = iface.Test_filter(SSession.getToken(), filter);
		}
	}
	public static List<STestBasicReader> list(long problem_id) throws SException {
		ListCommand command = new ListCommand(problem_id);
		SThriftClient.call(command);
		List<STestBasicReader> result = new ArrayList<STestBasicReader>(); 
		for (TestStruct struct : command.getList()) result.add(new TestBasicWrap(struct));
		return Collections.unmodifiableList(result);
	}
}
