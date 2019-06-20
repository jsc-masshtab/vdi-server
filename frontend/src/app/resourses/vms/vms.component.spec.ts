import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { VmsComponent } from './vms.component';

describe('TemplatesComponent', () => {
  let component: VmsComponent;
  let fixture: ComponentFixture<VmsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ VmsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VmsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
