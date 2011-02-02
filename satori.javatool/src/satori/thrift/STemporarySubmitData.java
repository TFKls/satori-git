package satori.thrift;

import static satori.thrift.SAttributeData.createAttrMap;
import static satori.thrift.SAttributeData.createBlobs;

import java.util.Collections;

import satori.attribute.SAttributeReader;
import satori.blob.SBlob;
import satori.common.SAssert;
import satori.common.SException;
import satori.session.SSession;
import satori.test.STemporarySubmitReader;
import satori.thrift.SAttributeData.AttributeWrap;
import satori.thrift.gen.TemporarySubmit;
import satori.thrift.gen.TemporarySubmitStruct;

public class STemporarySubmitData {
	static class TemporarySubmitWrap implements STemporarySubmitReader {
		private final TemporarySubmitStruct struct;
		private SAttributeReader result;
		public TemporarySubmitWrap(TemporarySubmitStruct struct) { this.struct = struct; }
		public void setResult(SAttributeReader result) { this.result = result; }
		@Override public boolean getPending() { return struct.isPending(); }
		@Override public SAttributeReader getResult() { return result; }
	}
	
	private static class LoadCommand implements SThriftCommand {
		private final long id;
		private TemporarySubmitWrap result;
		public STemporarySubmitReader getResult() { return result; }
		public LoadCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			TemporarySubmit.Iface iface = new TemporarySubmit.Client(SThriftClient.getProtocol());
			result = new TemporarySubmitWrap(iface.TemporarySubmit_get_struct(SSession.getToken(), id));
			result.setResult(new AttributeWrap(iface.TemporarySubmit_result_get_map(SSession.getToken(), id)));
		}
	}
	public static STemporarySubmitReader load(long id) throws SException {
		LoadCommand command = new LoadCommand(id);
		SThriftClient.call(command);
		return command.getResult();
	}
	
	private static class SubmitDataWrap implements SAttributeReader {
		private final SBlob submit;
		public SubmitDataWrap(SBlob submit) { this.submit = submit; }
		@Override public Iterable<String> getNames() { return Collections.singleton("content"); }
		@Override public boolean isBlob(String name) { return true; }
		@Override public String getString(String name) { return null; }
		@Override public SBlob getBlob(String name) { return submit; }
	}
	private static class CreateCommand implements SThriftCommand {
		private final SAttributeReader submit_data;
		private final SAttributeReader test_data;
		private long result;
		public long getResult() { return result; }
		public CreateCommand(SAttributeReader submit_data, SAttributeReader test_data) {
			this.submit_data = submit_data;
			this.test_data = test_data;
		}
		@Override public void call() throws Exception {
			TemporarySubmit.Iface iface = new TemporarySubmit.Client(SThriftClient.getProtocol());
			result = iface.TemporarySubmit_create(SSession.getToken(), createAttrMap(test_data), createAttrMap(submit_data)).getId();
		}
	}
	public static long create(SBlob submit, SAttributeReader test_data) throws SException {
		SAssert.assertNotNull(submit, "Submit is null");
		SAssert.assertNotNull(test_data, "Attribute map is null");
		SAttributeReader submit_data = new SubmitDataWrap(submit);
		createBlobs(submit_data);
		createBlobs(test_data);
		CreateCommand command = new CreateCommand(submit_data, test_data);
		SThriftClient.call(command);
		return command.getResult();
	}
}
