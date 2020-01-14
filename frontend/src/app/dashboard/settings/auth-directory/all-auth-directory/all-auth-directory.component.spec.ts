import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AuthenticationDirectoryComponent } from './all-auth-directory.component';

describe('TemplatesComponent', () => {
  let component: AuthenticationDirectoryComponent;
  let fixture: ComponentFixture<AuthenticationDirectoryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [AuthenticationDirectoryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AuthenticationDirectoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
